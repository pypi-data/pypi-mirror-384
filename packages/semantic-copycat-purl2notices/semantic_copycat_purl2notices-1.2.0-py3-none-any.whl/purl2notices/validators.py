"""Validators for purl2notices."""

from pathlib import Path
from typing import List, Optional, Tuple
from packageurl import PackageURL


class PurlValidator:
    """Validate Package URLs according to the spec."""
    
    @staticmethod
    def validate(purl_string: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a PURL string.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not purl_string or not purl_string.strip():
            return False, "Empty PURL string"

        try:
            # PackageURL will validate according to the spec
            parsed = PackageURL.from_string(purl_string.strip())

            # Additional validation
            if not parsed.type:
                return False, "PURL must have a type"

            if not parsed.name:
                return False, "PURL must have a name"

            if not parsed.version:
                return False, "PURL must have a version"

            return True, None

        except Exception as e:
            return False, str(e)

    @staticmethod
    def validate_and_parse(purl_string: str) -> Tuple[bool, Optional[str], Optional[PackageURL]]:
        """
        Validate a PURL string and return parsed object.

        Returns:
            Tuple of (is_valid, error_message, parsed_purl)
        """
        if not purl_string or not purl_string.strip():
            return False, "Empty PURL string", None

        try:
            # PackageURL will validate according to the spec
            parsed = PackageURL.from_string(purl_string.strip())

            # Additional validation
            if not parsed.type:
                return False, "PURL must have a type", None

            if not parsed.name:
                return False, "PURL must have a name", None

            return True, None, parsed

        except Exception as e:
            return False, str(e), None
    
    @staticmethod
    def validate_batch(purl_strings: List[str]) -> List[Tuple[str, bool, Optional[str]]]:
        """
        Validate multiple PURL strings.
        
        Returns:
            List of tuples (purl_string, is_valid, error_message)
        """
        results = []
        for purl in purl_strings:
            is_valid, error = PurlValidator.validate(purl)
            results.append((purl, is_valid, error))
        return results


class FileValidator:
    """Validate input files."""
    
    @staticmethod
    def validate_kissbom(file_path: Path) -> Tuple[bool, List[str], Optional[str]]:
        """
        Validate a KissBOM file.

        Returns:
            Tuple of (is_valid, purl_list, error_message)
        """
        if not file_path.exists():
            return False, [], f"File not found: {file_path}"

        if not file_path.is_file():
            return False, [], f"Not a file: {file_path}"
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            purls = []
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Basic PURL format check
                if not line.startswith('pkg:'):
                    return False, [], f"Line {line_num}: Invalid PURL format (must start with 'pkg:')"

                purls.append(line)

            if not purls:
                return False, [], "No valid PURLs found in file"

            return True, purls, None

        except Exception as e:
            return False, [], f"Error reading file: {e}"
    
    @staticmethod
    def is_cache_file(file_path: Path) -> bool:
        """Check if a file is a CycloneDX cache file."""
        # Also recognize .cdx.json and .cache.json extensions without content check
        if file_path.name.endswith('.cdx.json') or file_path.name.endswith('.cache.json'):
            return True

        if not file_path.exists() or not file_path.is_file():
            return False
        
        # Check by extension and content
        if file_path.suffix == '.json' or file_path.name.endswith('.cdx.json') or file_path.name.endswith('.cache.json'):
            try:
                import json
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Check for CycloneDX structure
                    return 'bomFormat' in data and data['bomFormat'] == 'CycloneDX'
            except:
                pass

        return False
    
    @staticmethod
    def is_archive_file(file_path: Path, custom_extensions: Optional[list] = None) -> bool:
        """Check if a file is a supported archive file.
        
        Args:
            file_path: Path to check
            custom_extensions: Optional list of custom extensions to use instead of defaults
        """
        from .constants import ARCHIVE_EXTENSIONS
        
        # Use custom extensions if provided, otherwise use defaults
        if custom_extensions:
            archive_extensions = custom_extensions
        else:
            archive_extensions = ARCHIVE_EXTENSIONS
        
        for ext in archive_extensions:
            if file_path.name.endswith(ext):
                return True
        return False
    
    @staticmethod
    def detect_input_type(input_path: str) -> str:
        """
        Detect the type of input.
        
        Returns one of: 'purl', 'kissbom', 'cache', 'archive', 'directory', 'unknown'
        """
        # Check if it's a PURL
        if input_path.startswith('pkg:'):
            return 'purl'
        
        path = Path(input_path)
        
        # Check if it's a directory
        if path.is_dir():
            return 'directory'
        
        # Check if it's a file
        if path.is_file():
            # Check if it's a cache file
            if FileValidator.is_cache_file(path):
                return 'cache'
            
            # Check if it's an archive file
            if FileValidator.is_archive_file(path):
                return 'archive'
            
            # Check if it's a KissBOM file
            is_valid, _, _ = FileValidator.validate_kissbom(path)
            if is_valid:
                return 'kissbom'
        
        return 'unknown'