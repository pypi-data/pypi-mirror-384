from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict, Counter
import os
import logging
import warnings
import subprocess
import shutil
import tempfile
import concurrent.futures
import hashlib
import base64
import jwt
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class WhosePIIGuardian:
    """
    Detects and masks PII in text using a hybrid approach.
    
    Supports both cloud-based inference (default) and local inference (fallback).
    Model: whose-pii-guardian-v2
    """
    
    def __init__(
        self, 
        user_api_key: Optional[str] = None,
        local_mode: bool = False,
        local_fallback: bool = True,
        config_path: Optional[str] = None
    ):
        """
        Initialize the PII Guardian.
        
        Args:
            user_api_key: User's JWT API key for authentication and usage tracking
            local_mode: Force local inference (requires heavy dependencies)
            local_fallback: Fall back to local models if cloud fails
            config_path: Path to configuration file
        """
        self._model_version = "whose-pii-guardian-v2"
        self.user_api_key = user_api_key
        self.local_mode = local_mode
        self.local_fallback = local_fallback
        
        # Extract RunPod credentials from JWT or environment variables
        self.runpod_api_key, self.endpoint_id = self._extract_runpod_credentials(user_api_key)
        
        # Fallback to environment variables if not found in JWT
        if not self.runpod_api_key:
            self.runpod_api_key = os.getenv("RUNPOD_API_KEY")
        if not self.endpoint_id:
            self.endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")
        
        # Initialize cloud client
        self.api_client = None
        if not local_mode:
            try:
                from .client import RunPodAPIClient, ClientConfig
                
                if config_path:
                    config = ClientConfig.from_file(config_path)
                else:
                    config = ClientConfig.from_env()
                
                # Use hardcoded credentials
                config.runpod_api_key = self.runpod_api_key
                config.endpoint_id = self.endpoint_id
                config.local_fallback = local_fallback
                
                if config.is_valid():
                    self.api_client = RunPodAPIClient(config)
                    logger.info("PII Guardian initialized with cloud inference")
                else:
                    if not local_fallback:
                        raise ValueError(
                            "Cloud inference requires a valid user API key. "
                            "Provide user_api_key or enable local_fallback=True"
                        )
                    logger.warning("Cloud credentials not available, using local mode")
                    self.local_mode = True
                    
            except ImportError as e:
                logger.warning(f"Cloud dependencies not available: {e}")
                if not local_fallback:
                    raise ImportError(
                        "Cloud inference dependencies not available. "
                        "Install with: pip install anotiai-pii-masker[cloud]"
                    )
                self.local_mode = True
        
        # Initialize local models if needed
        if self.local_mode or (local_fallback and self.api_client is None):
            self._init_local_models()
        
        logger.info(f"PII Guardian initialized with model: {self._model_version}")
    
    def _extract_runpod_credentials(self, user_api_key: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract and decrypt RunPod credentials from JWT using JWT secret + user ID.
        
        Args:
            user_api_key: The user's JWT API key containing encrypted RunPod credentials
            
        Returns:
            Tuple of (runpod_api_key, endpoint_id) or (None, None) if extraction fails
        """
        if not user_api_key:
            return None, None
            
        try:
            # Get JWT secret (same as used in generate_key.py)
            jwt_secret = os.getenv("JWT_SECRET_KEY", "sDvjQVdmGDLUsvPeNySxBOqiIZ-bdHZHDlqxWC9YNkY")
            
            # Decode JWT to get payload (without signature verification for now)
            decoded = jwt.decode(user_api_key, options={"verify_signature": False})
            user_id = decoded.get("sub")
            
            if not user_id:
                logger.warning("No user ID found in JWT")
                return None, None
            
            # Check if encrypted credentials are present
            if "encrypted_runpod" not in decoded or "encrypted_endpoint" not in decoded:
                logger.info("No encrypted RunPod credentials found in JWT")
                return None, None
            
            # Create user-specific encryption key using JWT secret + user_id
            encryption_key = hashlib.sha256(f"{jwt_secret}_{user_id}".encode()).digest()
            fernet = Fernet(base64.urlsafe_b64encode(encryption_key))
            
            # Decrypt credentials
            encrypted_runpod = base64.urlsafe_b64decode(decoded["encrypted_runpod"])
            encrypted_endpoint = base64.urlsafe_b64decode(decoded["encrypted_endpoint"])
            
            runpod_api_key = fernet.decrypt(encrypted_runpod).decode()
            endpoint_id = fernet.decrypt(encrypted_endpoint).decode()
            
            logger.info("Successfully extracted RunPod credentials from JWT")
            return runpod_api_key, endpoint_id
            
        except Exception as e:
            logger.warning(f"Failed to extract RunPod credentials from JWT: {e}")
            return None, None
    
    def _init_local_models(self):
        """Initialize local models (heavy dependencies required)."""
        try:
            from .Classification import config
            from .Classification.inference import PiiContextClassifier
            from .Classification.inference_baseline import BaselineClassifier
            from .extraction_engine.presidio_pii import PresidioPiiDetector
            from .extraction_engine.spacy_pii import SpacyPiiDetector
            from .extraction_engine.qa_pii import QaPiiDetector
            
            # Get a writable directory for model storage
            # Use user cache directory to avoid permission issues in system installations
            try:
                import appdirs
                cache_dir = appdirs.user_cache_dir("anotiai-pii-masker", "AnotiAI")
            except ImportError:
                # Fallback to standard cache directory
                import tempfile
                cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "anotiai-pii-masker")
            
            models_dir = os.path.join(cache_dir, "MODELS")
            logger.info(f"Using models directory: {models_dir}")
            
            # Check if models exist, if not, download them
            if not os.path.exists(models_dir):
                logger.info("Local models not found. Downloading from Hugging Face Hub...")
                self._download_models_from_huggingface(models_dir)
            else:
                # Check if required model directories exist
                required_models = ["roberta_large", "debarta_large", "baseline_model"]
                missing_models = []
                for model in required_models:
                    model_path = os.path.join(models_dir, model)
                    if not os.path.exists(model_path):
                        missing_models.append(model)
                
                if missing_models:
                    logger.info(f"Missing models: {missing_models}. Downloading from Hugging Face Hub...")
                    self._download_models_from_huggingface(models_dir)
            
            # All dependencies are checked in _download_models_from_huggingface
            
            self.presidio_detector = PresidioPiiDetector()
            self.spacy_detector = SpacyPiiDetector()
            self.qa_detector = QaPiiDetector(model_name="deepset/deberta-v3-large-squad2")
            self.qa_detector2 = QaPiiDetector(model_name="deepset/xlm-roberta-large-squad2")
            # Initialize classifiers with better error handling
            try:
                self.roberta_classifier = PiiContextClassifier(model_path=os.path.join(models_dir, "roberta_large"))
                logger.info("RoBERTa classifier loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load RoBERTa classifier: {e}")
                raise RuntimeError(f"Could not load RoBERTa classifier: {e}")
            
            try:
                self.debarta_classifier = PiiContextClassifier(model_path=os.path.join(models_dir, "debarta_large"))
                logger.info("DeBERTa classifier loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load DeBERTa classifier: {e}")
                raise RuntimeError(f"Could not load DeBERTa classifier: {e}")
            
            try:
                self.baseline_classifier = BaselineClassifier(model_path=os.path.join(models_dir, "baseline_model"))
                logger.info("Baseline classifier loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load baseline classifier: {e}")
                raise RuntimeError(f"Could not load baseline classifier: {e}")
            self.tracker = defaultdict(int)
            self.config = config

            self._supported_entities = set(self.presidio_detector.get_supported_entities()) | set(self.spacy_detector.get_supported_entities())
            logger.info("Local models initialized successfully")
            
        except ImportError as e:
            if self.local_mode:
                raise ImportError(
                    f"Local inference dependencies not available: {e}. "
                    "Install with: pip install anotiai-pii-masker[local]"
                )
            logger.warning(f"Local models not available for fallback: {e}")
            self.local_fallback = False
    
    def _ensure_local_dependencies(self):
        """Ensure all required dependencies for local inference are available."""
        logger.info("Checking local inference dependencies...")
        
        # Check spaCy model
        try:
            import spacy
            nlp = spacy.load("en_core_web_lg")
            logger.info("✅ spaCy English model (en_core_web_lg) is available")
        except OSError:
            logger.info("📥 spaCy English model not found, downloading...")
            try:
                result = subprocess.run([
                    "python", "-m", "spacy", "download", "en_core_web_lg"
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    logger.info("✅ Successfully downloaded spaCy English model")
                else:
                    raise RuntimeError(f"Failed to download spaCy model: {result.stderr}")
            except Exception as e:
                raise RuntimeError(f"Could not download spaCy model: {e}. Please run: python -m spacy download en_core_web_lg")
        except Exception as e:
            raise RuntimeError(f"spaCy model check failed: {e}")

        # Check huggingface-hub
        try:
            import huggingface_hub
            logger.info("✅ huggingface-hub is available")
        except ImportError:
            raise RuntimeError("huggingface-hub not found. Please install with: pip install anotiai-pii-masker[local]")
        
        # Check git and git lfs
        try:
            # Check if git is available
            subprocess.run(["git", "--version"], check=True, capture_output=True, timeout=10)
            logger.info("✅ Git is available")
            
            # Check if git lfs is available
            result = subprocess.run(["git", "lfs", "version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("✅ Git LFS is available")
            else:
                raise RuntimeError("Git LFS not found. Please install with: apt-get install git-lfs")
            
            # Initialize git lfs
            subprocess.run(["git", "lfs", "install"], check=True, capture_output=True, timeout=10)
            logger.info("✅ Git LFS initialized")
            
        except FileNotFoundError:
            raise RuntimeError("Git not found. Please install git first.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git LFS setup failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Git/LFS check failed: {e}")
        
        logger.info("✅ All local inference dependencies are available")
    
    def _download_models_from_huggingface(self, models_dir: str):
        """Download models from Hugging Face Hub."""
        try:
            # Create models directory
            os.makedirs(models_dir, exist_ok=True)
            
            # Check all local dependencies
            self._ensure_local_dependencies()
            
            # Model repositories on Hugging Face Hub
            model_repos = {
                "roberta_large": "ForTheLoveOfML0/roberta_large",
                "debarta_large": "ForTheLoveOfML0/debarta_large",
                "baseline_model": "ForTheLoveOfML0/baseline-model"
            }
            
            # Download each model
            for model_name, repo_id in model_repos.items():
                model_path = os.path.join(models_dir, model_name)
                
                if not os.path.exists(model_path):
                    logger.info(f"Downloading {model_name} from {repo_id}...")
                    
                    # Try using huggingface-hub CLI first
                    try:
                        result = subprocess.run([
                            "hf", "download", 
                            repo_id,
                            "--local-dir", model_path
                        ], capture_output=True, text=True, timeout=600)  # Increased timeout to 10 minutes
                        
                        if result.returncode == 0:
                            logger.info(f"Successfully downloaded {model_name}")
                            # Validate the downloaded model
                            if self._validate_downloaded_model(model_path, model_name):
                                logger.info(f"Model {model_name} validation successful")
                            else:
                                logger.warning(f"Model {model_name} validation failed, but files were downloaded")
                        else:
                            logger.warning(f"huggingface-cli failed for {model_name}: {result.stderr}")
                            # Try alternative download method
                            self._download_model_alternative(repo_id, model_path, model_name)
                            
                    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                        logger.warning(f"huggingface-cli not available for {model_name}: {e}")
                        # Try alternative download method
                        self._download_model_alternative(repo_id, model_path, model_name)
            
            logger.info("Model download completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to download models: {e}")
            raise RuntimeError(
                f"Could not download models from Hugging Face Hub: {e}. "
                "Please ensure you have internet connectivity and try again. "
                "You can also manually download models using:\n"
                "hf download ForTheLoveOfML0/roberta_large --local-dir ./MODELS/roberta_large\n"
                "hf download ForTheLoveOfML0/deberta_large --local-dir ./MODELS/debarta_large\n"
                "hf download ForTheLoveOfML0/baseline-model --local-dir ./MODELS/baseline_model"
            )
    
    def _download_model_alternative(self, repo_id: str, model_path: str, model_name: str):
        """Alternative download method using git clone with Git LFS."""
        try:
            # Remove existing directory if it exists
            if os.path.exists(model_path):
                shutil.rmtree(model_path)
            
            # Clone the repository using git
            repo_url = f"https://huggingface.co/{repo_id}"
            logger.info(f"Cloning {model_name} from {repo_url}...")
            
            # Dependencies already checked in _download_models_from_huggingface
            
            # Clone the repository
            result = subprocess.run([
                "git", "clone", repo_url, model_path
            ], capture_output=True, text=True, timeout=600)  # 10 minutes timeout
            
            if result.returncode == 0:
                logger.info(f"Successfully cloned {model_name}")
                return True
            else:
                logger.error(f"Git clone failed for {model_name}: {result.stderr}")
                raise RuntimeError(f"Git clone failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Git clone download failed for {model_name}: {e}")
            raise RuntimeError(f"Could not clone {model_name}: {e}")
    
    def _validate_downloaded_model(self, model_path: str, model_name: str) -> bool:
        """Validate that the downloaded model has the required files."""
        try:
            if not os.path.exists(model_path):
                return False
            
            # Check for essential files based on model type
            if model_name == "baseline_model":
                required_files = ["logistic_regression_model.joblib", "tfidf_vectorizer.joblib"]
            else:
                # For transformer models, check for essential files
                required_files = ["config.json"]
                # Check for either model.safetensors or pytorch_model.bin
                has_safetensors = os.path.exists(os.path.join(model_path, "model.safetensors"))
                has_pytorch = os.path.exists(os.path.join(model_path, "pytorch_model.bin"))
                if not (has_safetensors or has_pytorch):
                    logger.warning(f"Model {model_name} missing model weights file")
                    return False
            
            # Check if all required files exist and are not empty
            for file in required_files:
                file_path = os.path.join(model_path, file)
                if not os.path.exists(file_path):
                    logger.warning(f"Model {model_name} missing required file: {file}")
                    return False
                if os.path.getsize(file_path) == 0:
                    logger.warning(f"Model {model_name} has empty file: {file}")
                    return False
            
            logger.info(f"Model {model_name} validation passed")
            return True
                    
        except Exception as e:
            logger.warning(f"Model validation failed for {model_name}: {e}")
            return False
    
    
    def _use_cloud_inference(self) -> bool:
        """Determine whether to use cloud inference."""
        return not self.local_mode and self.api_client is not None
    
    def mask_text(self, text: str, confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Detect and mask PII in the provided text.
        
        This method identifies personally identifiable information in the input text and replaces
        it with redacted placeholders while maintaining a mapping for potential restoration.
        
        Args:
            text (str): The text to process for PII detection and masking
            confidence_threshold (float, optional): Minimum confidence threshold for PII detection (0.0-1.0). 
                                                  Higher values = more strict detection. Default: 0.5
            
        Returns:
            Dict[str, Any]: A dictionary containing:
                - masked_text (str): Text with PII replaced by placeholders like [REDACTED_NAME_1]
                - pii_map (Dict): Mapping of placeholders to original PII data
                - entities_found (int): Number of PII entities detected
                - confidence_threshold (float): Threshold used for detection
                - usage (Dict): Token usage information for billing/monitoring
                    - input_tokens (int): Original text token count
                    - output_tokens (int): Masked text + PII map token count
                    - total_tokens (int): Total tokens processed
        
        Raises:
            ValueError: If user API key is required but not provided (cloud mode)
            RuntimeError: If local models are not initialized (local mode)
            APIError: If cloud inference fails
            AuthenticationError: If API authentication fails
            NetworkError: If network connectivity issues occur
            
        Example:
            >>> guardian = WhosePIIGuardian(user_api_key="your_key")
            >>> result = guardian.mask_text("My name is John Doe and email is john@example.com")
            >>> print(result['masked_text'])
            "My name is [REDACTED_NAME_1] and email is [REDACTED_EMAIL_1]"
            >>> print(result['pii_map']['__TOKEN_1__']['value'])
            "John Doe"
        """
        if self._use_cloud_inference():
            if not self.user_api_key:
                raise ValueError("User API key is required for cloud inference")
            try:
                return self.api_client.mask_text(text, self.user_api_key, confidence_threshold)
            except Exception as e:
                logger.warning(f"Cloud inference failed: {e}")
                if self.local_fallback:
                    logger.info("Falling back to local inference")
                    return self._mask_text_local(text, confidence_threshold)
                else:
                    raise
        else:
            return self._mask_text_local(text, confidence_threshold)
    
    def unmask_text(self, masked_text: str, pii_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Restore the original text from a masked version using the PII map.
        
        This method reverses the masking process by replacing placeholders with their original
        PII values based on the provided mapping dictionary.
        
        Args:
            masked_text (str): The masked text containing placeholders like [REDACTED_NAME_1]
            pii_map (Dict[str, Any]): The PII mapping dictionary from mask_text() containing
                                    placeholder-to-original-value mappings
            
        Returns:
            Dict[str, Any]: A dictionary containing:
                - unmasked_text (str): Original text with PII restored
                - entities_restored (int): Number of entities restored
                - usage (Dict): Token usage information for billing/monitoring
                    - input_tokens (int): Masked text + PII map token count
                    - output_tokens (int): Unmasked text token count
                    - total_tokens (int): Total tokens processed
        
        Raises:
            ValueError: If user API key is required but not provided (cloud mode)
            RuntimeError: If local models are not initialized (local mode)
            APIError: If cloud inference fails
            AuthenticationError: If API authentication fails
            NetworkError: If network connectivity issues occur
            
        Example:
            >>> # Using result from mask_text()
            >>> unmask_result = guardian.unmask_text(result['masked_text'], result['pii_map'])
            >>> print(unmask_result['unmasked_text'])
            "My name is John Doe and email is john@example.com"
            >>> print(unmask_result['entities_restored'])
            2
        """
        if self._use_cloud_inference():
            if not self.user_api_key:
                raise ValueError("User API key is required for cloud inference")
            try:
                return self.api_client.unmask_text(masked_text, pii_map, self.user_api_key)
            except Exception as e:
                logger.warning(f"Cloud inference failed: {e}")
                if self.local_fallback:
                    logger.info("Falling back to local inference")
                    return self._unmask_text_local(masked_text, pii_map)
                else:
                    raise
        else:
            return self._unmask_text_local(masked_text, pii_map)
    
    def detect_pii(self, text: str, confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Detect PII entities in text without masking.
        
        This method analyzes the input text to identify personally identifiable information
        and returns detailed information about detected entities without modifying the text.
        
        Args:
            text (str): The text to analyze for PII detection
            confidence_threshold (float, optional): Minimum confidence threshold for detection (0.0-1.0).
                                                  Higher values = more strict detection. Default: 0.5
            
        Returns:
            Dict[str, Any]: A dictionary containing:
                - entities_found (int): Number of PII entities detected
                - pii_results (List[Dict]): List of detected PII entities with details:
                    - value (str): Original PII value
                    - type (str): PII type (name, email, phone, etc.)
                    - start (int): Start position in text
                    - end (int): End position in text
                    - confidence (float): Detection confidence (0.0-1.0)
                - classification (str): Text classification result (pii_disclosure, no_pii, etc.)
                - confidence (float): Classification confidence
                - usage (Dict): Token usage information for billing/monitoring
                    - input_tokens (int): Original text token count
                    - output_tokens (int): Detection results token count
                    - total_tokens (int): Total tokens processed
        
        Raises:
            ValueError: If user API key is required but not provided (cloud mode)
            RuntimeError: If local models are not initialized (local mode)
            APIError: If cloud inference fails
            AuthenticationError: If API authentication fails
            NetworkError: If network connectivity issues occur
            
        Example:
            >>> result = guardian.detect_pii("My name is John Doe and email is john@example.com")
            >>> print(f"Found {result['entities_found']} entities")
            "Found 2 entities"
            >>> for entity in result['pii_results']:
            ...     print(f"- {entity['type']}: {entity['value']} (confidence: {entity['confidence']})")
            "- name: John Doe (confidence: 0.95)"
            "- email: john@example.com (confidence: 0.98)"
        """
        if self._use_cloud_inference():
            if not self.user_api_key:
                raise ValueError("User API key is required for cloud inference")
            try:
                return self.api_client.detect_pii(text, self.user_api_key, confidence_threshold)
            except Exception as e:
                logger.warning(f"Cloud inference failed: {e}")
                if self.local_fallback:
                    logger.info("Falling back to local inference")
                    pii_entities = self._detect_local(text)
                    return {
                        "entities_found": len(pii_entities['pii_results']),
                        "pii_results": pii_entities['pii_results'],
                        "classification": pii_entities['classification'],
                        "confidence": pii_entities['confidence'],
                        "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
                    }
                else:
                    raise
        else:
            pii_entities = self._detect_local(text)
            return {
                "entities_found": len(pii_entities['pii_results']),
                "pii_results": pii_entities['pii_results'],
                "classification": pii_entities['classification'],
                "confidence": pii_entities['confidence'],
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            }
    
    def get_model_version(self) -> str:
        """
        Return the version of the loaded PII detection model.
        
        Returns:
            str: Model version identifier
            
        Example:
            >>> version = guardian.get_model_version()
            >>> print(version)
            "whose-pii-guardian-v2"
        """
        if self._use_cloud_inference():
            if not self.user_api_key:
                raise ValueError("User API key is required for cloud inference")
            try:
                result = self.api_client.get_model_version(self.user_api_key)
                return result.get("model_version", self._model_version)
            except Exception as e:
                logger.warning(f"Failed to get cloud model version: {e}")
        
        return self._model_version
    
    def get_supported_entities(self) -> List[str]:
        """
        Return a list of PII entity types supported by the detector.
        
        Returns:
            List[str]: List of supported PII entity types
            
        Example:
            >>> entities = guardian.get_supported_entities()
            >>> print(entities)
            ['email', 'phone', 'person', 'credit_card', 'ssn', 'passport', 'license', 'address', 'url', 'ip_address']
        """
        if hasattr(self, '_supported_entities'):
            return list(self._supported_entities)
        else:
            # Default supported entities for cloud mode
            return [
                "email", "phone", "person", "credit_card", "ssn", 
                "passport", "license", "address", "url", "ip_address"
            ]
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the service.
        
        Returns:
            Dict[str, Any]: A dictionary containing:
                - status (str): "healthy" or "unhealthy"
                - mode (str): "cloud" or "local" (for local mode)
                - service (str): Service identifier
                - error (str): Error message if unhealthy (optional)
                
        Example:
            >>> health = guardian.health_check()
            >>> print(f"Service status: {health['status']}")
            "Service status: healthy"
        """
        if self._use_cloud_inference():
            try:
                return self.api_client.health_check()
            except Exception as e:
                return {
                    "status": "unhealthy", 
                    "error": str(e),
                    "service": "anotiai-pii-guardian"
                }
        else:
            return {
                "status": "healthy",
                "mode": "local",
                "service": "anotiai-pii-guardian"
            }
    
    def _mask_text_local(self, text: str, confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """Local implementation of text masking with context-aware logic."""
        if not hasattr(self, 'presidio_detector'):
            raise RuntimeError("Local models not initialized")
        
        logger.info(f"Starting text masking for text of length: {len(text)}")
        pii_detection_result = self._detect_local(text)
        masked_text = text
        pii_map = {}

        classification = pii_detection_result['classification']
        entities = pii_detection_result['pii_results']

        if not entities:
            logger.info("No PII entities found to mask - returning original text")
            from .utils import count_tokens
            return {
                "masked_text": text,
                "pii_map": {},
                "entities_found": 0,
                "confidence_threshold": confidence_threshold,
                "usage": {
                    "input_tokens": count_tokens(text),
                    "output_tokens": count_tokens(text),
                    "total_tokens": count_tokens(text) * 2
                }
            }

        entities_to_mask = []
        if classification == "pii_disclosure":
            logger.info("Classification is 'pii_disclosure', preparing to mask all detected entities.")
            entities_to_mask = entities
        elif classification == "pii_inquiry_or_public_mention":
            CORE_HIGH_SENSITIVITY_PII = {"SSN", "CREDIT_CARD", "PASSPORT", "LICENSE", "CRYPTO", "API_KEY"}
            entities_to_mask = [
                entity for entity in entities if entity.get('type') in CORE_HIGH_SENSITIVITY_PII
            ]
            logger.info(
                f"Classification is 'pii_inquiry_or_public_mention', "
                f"preparing to mask {len(entities_to_mask)} high-sensitivity entities."
            )
        else: # 'no_pii' or any other class
            logger.info(f"Classification is '{classification}', no entities will be masked.")
            entities_to_mask = []

        if not entities_to_mask:
            logger.info("No entities to mask after applying context-aware rules - returning original text.")
            from .utils import count_tokens
            return {
                "masked_text": text,
                "pii_map": {},
                "entities_found": 0,
                "confidence_threshold": confidence_threshold,
                "usage": {
                    "input_tokens": count_tokens(text),
                    "output_tokens": count_tokens(text),
                    "total_tokens": count_tokens(text) * 2
                }
            }
        
        logger.info(f"Masking {len(entities_to_mask)} PII entities.")
        sorted_pii = sorted(entities_to_mask, key=lambda x: x['start'], reverse=True)
        for i, entity in enumerate(sorted_pii):
            if entity['confidence'] < confidence_threshold:
                pii_map[f"__TOKEN_{i+1}__"] = {
                    'value': entity['value'],
                    'label': entity['type'],
                    'confidence': entity['confidence'],
                    'placeholder': entity['value'],
                }
                continue
            self.tracker[entity['type']] += 1
            placeholder = f"[REDACTED_{entity['type'].upper()}_{self.tracker[entity['type']]}]"
            masked_text = masked_text[:entity['start']] + placeholder + masked_text[entity['end']:]
        
            pii_map[f"__TOKEN_{i+1}__"] = {
                'value': entity['value'],
                'label': entity['type'],
                'confidence': entity['confidence'],
                'placeholder': placeholder,
            }
            logger.debug(f"Masked entity {i+1}: {entity['type']} -> {placeholder}")
            
        logger.info(f"Text masking completed. Created {len(pii_map)} masked entities map")
        
        from .utils import count_tokens
        return {
            "masked_text": masked_text,
            "pii_map": pii_map,
            "entities_found": len(pii_map),
            "confidence_threshold": confidence_threshold,
            "usage": {
                "input_tokens": count_tokens(text),
                "output_tokens": count_tokens(masked_text) + count_tokens(str(pii_map)),
                "total_tokens": count_tokens(text) + count_tokens(masked_text) + count_tokens(str(pii_map))
            }
        }
    
    def _unmask_text_local(self, masked_text: str, pii_map: Dict[str, Any]) -> Dict[str, Any]:
        """Local implementation of text unmasking."""
        unmasked_text = masked_text
        for key, value in pii_map.items():
            # Handle both dict and PIIEntity object formats
            if hasattr(value, 'placeholder') and hasattr(value, 'value'):
                # PIIEntity object (from FastAPI)
                placeholder = value.placeholder
                original_value = value.value
            else:
                # Dictionary format
                placeholder = value['placeholder']
                original_value = value['value']
            
            unmasked_text = unmasked_text.replace(placeholder, original_value)
        
        from .utils import count_tokens
        return {
            "unmasked_text": unmasked_text,
            "entities_restored": len(pii_map),
            "usage": {
                "input_tokens": count_tokens(masked_text) + count_tokens(pii_map),
                "output_tokens": count_tokens(unmasked_text),
                "total_tokens": count_tokens(masked_text) + count_tokens(pii_map) + count_tokens(unmasked_text)
            }
        }
    
    def _detect_local(self, text: str) -> Dict[str, Any]:
        """Local implementation of PII detection with parallel execution."""
        if not hasattr(self, 'roberta_classifier'):
            raise RuntimeError("Local models not initialized")

        # Use ThreadPoolExecutor to run model inferences in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all classification and extraction tasks
            future_rb = executor.submit(self.roberta_classifier.predict_single, text)
            future_db = executor.submit(self.debarta_classifier.predict_single, text)
            future_bl = executor.submit(self.baseline_classifier.predict_single, text)
            
            future_presidio = executor.submit(self.presidio_detector.detect, text)
            future_spacy = executor.submit(self.spacy_detector.detect, text)
            future_qa1 = executor.submit(self.qa_detector.detect, text, confidence_threshold=0.5/1000)
            future_qa2 = executor.submit(self.qa_detector2.detect, text, confidence_threshold=0.5/1000)

            # Retrieve results as they complete
            rb_results = future_rb.result()
            db_results = future_db.result()
            bl_results = future_bl.result()
            
            presidio_results = future_presidio.result()
            spacy_results = future_spacy.result()
            qa_results = future_qa1.result()
            qa_results2 = future_qa2.result()

        # Perform classification aggregation
        classification, confidence, method = self._aggregate_predictions(rb_results, db_results, bl_results)
        classification = self.config.ID_TO_LABEL[classification]

        if not classification:
            return {
                "classification": "ERROR",
                "confidence": 0.0,
                "pii_results": []
            }

        logger.info(f"Text classified as '{classification}' with {confidence:.2f} confidence.")

        # Perform PII extraction consolidation
        all_pii = []
        all_pii.extend(presidio_results)
        all_pii.extend(spacy_results)
        all_pii.extend(qa_results)
        all_pii.extend(qa_results2)
        
        logger.info(f"Raw detection results - Presidio: {len(presidio_results)}, spaCy: {len(spacy_results)}, QA1: {len(qa_results)}, QA2: {len(qa_results2)}")

        # Consolidate and Deduplicate Results
        final_pii = self._consolidate_and_deduplicate(all_pii)
        logger.info(f"Found {len(final_pii)} unique PII entities after deduplication")
        
        # Log entity types found
        entity_types = [entity.get('type', 'unknown') for entity in final_pii]
        logger.info(f"Entity types found: {dict(Counter(entity_types))}")

        # Return the original classification and all found entities
        return {
            "classification": classification,
            "confidence": confidence,
            "pii_results": final_pii
        }
    
    def _aggregate_predictions(self, rb_results, db_results, bl_results):
        """Aggregate predictions from multiple models."""
        predictions = [
            rb_results['predicted_class_id'],
            db_results['predicted_class_id'], 
            bl_results['predicted_class_id']
        ]
        confidences = [
            rb_results['confidence'],
            db_results['confidence'],
            bl_results['confidence']
        ]
        
        # Count votes
        vote_counts = Counter(predictions)
        max_votes = max(vote_counts.values())
        
        # If there's a clear majority, return it with average confidence of winning votes
        if max_votes > 1:
            winning_class = max(vote_counts, key=vote_counts.get)
            # Calculate average confidence of the winning votes
            winning_confidences = [conf for pred, conf in zip(predictions, confidences) if pred == winning_class]
            aggregate_confidence = sum(winning_confidences) / len(winning_confidences)
            return winning_class, aggregate_confidence, "majority_vote"
        
        # Otherwise, use confidence-weighted voting for ties
        confidence_scores = {0: 0, 1: 0, 2: 0}
        for pred, conf in zip(predictions, confidences):
            confidence_scores[pred] += conf
        
        winning_class = max(confidence_scores, key=confidence_scores.get)
        # For confidence-weighted voting, use the confidence of the winning model
        winning_confidence = max(confidences)
        return winning_class, winning_confidence, "confidence_weighted"

    def _consolidate_and_deduplicate(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove overlapping entities from multiple detector sources, keeping the one
        with the highest confidence score.
        """
        if not entities:
            return []

        # Sort by confidence score in descending order to prioritize high-confidence entities
        entities.sort(key=lambda x: x.get('confidence', 0.0), reverse=True)

        unique_entities = []
        seen_ranges = set()

        for entity in entities:
            start, end = entity['start'], entity['end']
            # Check if the range of this entity overlaps with an already added entity
            if not any(start < seen_end and end > seen_start for seen_start, seen_end in seen_ranges):
                unique_entities.append(entity)
                seen_ranges.add((start, end))
        
        # Sort by start position for readability
        unique_entities.sort(key=lambda x: x['start'])
        return unique_entities
