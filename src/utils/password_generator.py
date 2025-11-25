#!/usr/bin/env python3
"""
Personal Password Manager - Password Generation Utility
======================================================

This module provides comprehensive password generation functionality with multiple
generation methods, customizable options, and security features. It supports
random passwords, memorable passphrases, pattern-based generation, and custom
character sets to meet various security requirements.

Key Features:
- Multiple generation methods (random, memorable, pattern-based)
- Customizable character sets and length ranges
- Security rules (character diversity, exclusions)
- Cryptographically secure random number generation
- Batch password generation for efficiency
- Password strength analysis and recommendations
- Pattern matching for site-specific requirements

Security Features:
- Uses cryptographically secure random number generator
- Ensures character diversity in generated passwords
- Excludes confusing characters (0, O, l, 1) when requested
- Prevents common patterns and sequences
- Validates generated passwords meet minimum requirements

Author: Personal Password Manager
Version: 2.2.0
"""

import secrets
import string
import re
import logging
import json
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Configure logging for password generation operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GenerationMethod(Enum):
    """Enumeration of password generation methods"""
    RANDOM = "random"                    # Cryptographically random passwords
    MEMORABLE = "memorable"              # Dictionary-based passphrases
    PATTERN = "pattern"                  # Pattern-based generation
    PRONOUNCEABLE = "pronounceable"      # Semi-random pronounceable passwords
    CUSTOM = "custom"                    # Custom generation rules

class CharacterSet(Enum):
    """Enumeration of character set types"""
    LOWERCASE = "lowercase"              # a-z
    UPPERCASE = "uppercase"              # A-Z
    DIGITS = "digits"                    # 0-9
    SYMBOLS = "symbols"                  # Special characters
    SIMILAR = "similar"                  # Confusing characters (0, O, l, 1)
    CUSTOM = "custom"                    # User-defined characters

@dataclass
class GenerationOptions:
    """
    Configuration options for password generation
    
    This dataclass contains all configuration options for password generation,
    including character sets, length requirements, and security rules.
    """
    length: int = 16                                    # Password length
    min_length: int = 8                                 # Minimum allowed length
    max_length: int = 128                               # Maximum allowed length
    include_lowercase: bool = True                      # Include a-z
    include_uppercase: bool = True                      # Include A-Z
    include_digits: bool = True                         # Include 0-9
    include_symbols: bool = True                        # Include special chars
    exclude_similar: bool = True                        # Exclude 0, O, l, 1, etc.
    exclude_ambiguous: bool = False                     # Exclude { } [ ] ( ) / \ ' " ` ~ , ; . < >
    custom_characters: str = ""                         # Additional custom chars
    excluded_characters: str = ""                       # Specific chars to exclude
    require_each_type: bool = True                      # Require at least one from each selected type
    avoid_patterns: bool = True                         # Avoid keyboard patterns and sequences
    word_count: int = 4                                 # Number of words for memorable passwords
    word_separator: str = "-"                           # Separator for memorable passwords
    capitalize_words: bool = True                       # Capitalize words in memorable passwords
    add_numbers: bool = True                            # Add numbers to memorable passwords
    pattern_template: str = ""                          # Pattern template (e.g., "Llll-dddd-Ssss")
    
    def __post_init__(self):
        """Validate configuration options after initialization"""
        # Validate length constraints
        if self.length < self.min_length:
            self.length = self.min_length
        elif self.length > self.max_length:
            self.length = self.max_length
        
        # Ensure at least one character type is included
        if not any([self.include_lowercase, self.include_uppercase, 
                   self.include_digits, self.include_symbols]):
            self.include_lowercase = True
            self.include_uppercase = True
            self.include_digits = True

@dataclass
class GeneratedPassword:
    """
    Represents a generated password with metadata
    """
    password: str = field(repr=False)                   # The generated password (not shown in logs)
    strength_score: int = 0                             # Password strength score (0-100)
    entropy: float = 0.0                                # Entropy in bits
    character_types: Dict[str, bool] = field(default_factory=dict)  # Character types present
    generation_method: str = ""                         # Method used for generation
    meets_requirements: bool = True                     # Whether password meets all requirements
    warnings: List[str] = field(default_factory=list)  # Any warnings about the password
    recommendations: List[str] = field(default_factory=list)  # Recommendations for improvement

class PasswordGenerator:
    """
    Comprehensive password generation system
    
    This class provides multiple password generation methods with extensive
    customization options and security features. It uses cryptographically
    secure random number generation and includes built-in password strength
    analysis.
    
    Features:
    - Multiple generation algorithms
    - Customizable character sets and rules
    - Built-in word dictionary for memorable passwords
    - Pattern-based generation with templates
    - Batch generation for efficiency
    - Password strength analysis
    - Security validation and recommendations
    """
    
    # Default character sets
    LOWERCASE_CHARS = string.ascii_lowercase
    UPPERCASE_CHARS = string.ascii_uppercase
    DIGIT_CHARS = string.digits
    SYMBOL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Characters that are often confused
    SIMILAR_CHARS = "0O1lI|`"
    
    # Ambiguous characters that can cause issues
    AMBIGUOUS_CHARS = "{}[]()/'\"`,;.<>"
    
    # Common keyboard patterns to avoid
    KEYBOARD_PATTERNS = [
        "qwerty", "asdf", "zxcv", "123456", "abcdef",
        "qwertyuiop", "asdfghjkl", "zxcvbnm",
        "1234567890", "0987654321"
    ]
    
    def __init__(self, word_list_path: Optional[str] = None):
        """
        Initialize the password generator
        
        Args:
            word_list_path (str, optional): Path to custom word list file
        """
        self.word_list = self._load_word_list(word_list_path)
        logger.info(f"Password generator initialized with {len(self.word_list)} words")
    
    def generate_password(self, options: GenerationOptions = None, 
                         method: GenerationMethod = GenerationMethod.RANDOM) -> GeneratedPassword:
        """
        Generate a single password using the specified method
        
        Args:
            options (GenerationOptions, optional): Generation configuration
            method (GenerationMethod): Generation method to use
            
        Returns:
            GeneratedPassword: Generated password with metadata
            
        Raises:
            ValueError: If generation parameters are invalid
        """
        if options is None:
            options = GenerationOptions()
        
        try:
            # Generate password based on method
            if method == GenerationMethod.RANDOM:
                password = self._generate_random_password(options)
            elif method == GenerationMethod.MEMORABLE:
                password = self._generate_memorable_password(options)
            elif method == GenerationMethod.PATTERN:
                password = self._generate_pattern_password(options)
            elif method == GenerationMethod.PRONOUNCEABLE:
                password = self._generate_pronounceable_password(options)
            else:
                raise ValueError(f"Unsupported generation method: {method}")
            
            # Analyze generated password
            result = self._analyze_password(password, options, method.value)
            
            logger.debug(f"Generated password using {method.value} method, strength: {result.strength_score}")
            return result
            
        except Exception as e:
            logger.error(f"Password generation failed: {e}")
            raise ValueError(f"Password generation failed: {e}")
    
    def generate_batch(self, count: int, options: GenerationOptions = None,
                      method: GenerationMethod = GenerationMethod.RANDOM) -> List[GeneratedPassword]:
        """
        Generate multiple passwords in batch for efficiency
        
        Args:
            count (int): Number of passwords to generate
            options (GenerationOptions, optional): Generation configuration
            method (GenerationMethod): Generation method to use
            
        Returns:
            List[GeneratedPassword]: List of generated passwords
            
        Raises:
            ValueError: If parameters are invalid
        """
        if count <= 0:
            raise ValueError("Count must be positive")
        
        if count > 1000:
            raise ValueError("Batch size too large (max 1000)")
        
        passwords = []
        
        try:
            for i in range(count):
                password = self.generate_password(options, method)
                passwords.append(password)
            
            logger.info(f"Generated batch of {count} passwords using {method.value} method")
            return passwords
            
        except Exception as e:
            logger.error(f"Batch generation failed: {e}")
            raise ValueError(f"Batch generation failed: {e}")
    
    def _generate_random_password(self, options: GenerationOptions) -> str:
        """
        Generate a cryptographically random password
        
        Args:
            options (GenerationOptions): Generation configuration
            
        Returns:
            str: Generated random password
        """
        # Build character set based on options
        charset = self._build_character_set(options)
        
        if not charset:
            raise ValueError("No characters available for password generation")
        
        # Generate password with required character types
        password = self._generate_with_requirements(charset, options)
        
        return password
    
    def _generate_memorable_password(self, options: GenerationOptions) -> str:
        """
        Generate a memorable passphrase using dictionary words
        
        Args:
            options (GenerationOptions): Generation configuration
            
        Returns:
            str: Generated memorable password
        """
        if not self.word_list:
            raise ValueError("Word list not available for memorable password generation")
        
        words = []
        
        # Select random words
        for _ in range(options.word_count):
            word = secrets.choice(self.word_list)
            
            if options.capitalize_words:
                word = word.capitalize()
            
            words.append(word)
        
        # Join words with separator
        password = options.word_separator.join(words)
        
        # Add numbers if requested
        if options.add_numbers:
            numbers = ''.join(secrets.choice(string.digits) for _ in range(2))
            password += options.word_separator + numbers
        
        # Add symbols if requested and available
        if options.include_symbols:
            symbol = secrets.choice("!@#$%^&*")
            password += symbol
        
        return password
    
    def _generate_pattern_password(self, options: GenerationOptions) -> str:
        """
        Generate password based on a pattern template
        
        Pattern format:
        - L: Uppercase letter
        - l: Lowercase letter  
        - d: Digit
        - s: Symbol
        - ?: Any character from available set
        
        Args:
            options (GenerationOptions): Generation configuration
            
        Returns:
            str: Generated pattern-based password
        """
        if not options.pattern_template:
            # Use default pattern if none provided
            options.pattern_template = "Llllddss"
        
        password = ""
        charset = self._build_character_set(options)
        
        for char in options.pattern_template:
            if char == 'L':
                # Uppercase letter
                password += secrets.choice(self.UPPERCASE_CHARS)
            elif char == 'l':
                # Lowercase letter
                password += secrets.choice(self.LOWERCASE_CHARS)
            elif char == 'd':
                # Digit
                password += secrets.choice(self.DIGIT_CHARS)
            elif char == 's':
                # Symbol
                available_symbols = self._filter_characters(self.SYMBOL_CHARS, options)
                if available_symbols:
                    password += secrets.choice(available_symbols)
                else:
                    password += secrets.choice(charset)
            elif char == '?':
                # Any available character
                password += secrets.choice(charset)
            else:
                # Literal character
                password += char
        
        return password
    
    def _generate_pronounceable_password(self, options: GenerationOptions) -> str:
        """
        Generate a semi-random but pronounceable password
        
        Uses consonant-vowel patterns to create pronounceable passwords
        while maintaining reasonable security.
        
        Args:
            options (GenerationOptions): Generation configuration
            
        Returns:
            str: Generated pronounceable password
        """
        consonants = "bcdfghjklmnpqrstvwxyz"
        vowels = "aeiou"
        
        password = ""
        target_length = max(8, min(options.length, 20))  # Reasonable bounds for pronounceable
        
        # Start with consonant or vowel randomly
        use_consonant = secrets.choice([True, False])
        
        while len(password) < target_length:
            if use_consonant:
                char = secrets.choice(consonants)
            else:
                char = secrets.choice(vowels)
            
            # Randomly capitalize some letters
            if secrets.randbelow(4) == 0 and options.include_uppercase:
                char = char.upper()
            
            password += char
            use_consonant = not use_consonant
        
        # Add digits and symbols if requested
        if options.include_digits and len(password) < options.length:
            digits_to_add = min(2, options.length - len(password))
            for _ in range(digits_to_add):
                password += secrets.choice(self.DIGIT_CHARS)
        
        if options.include_symbols and len(password) < options.length:
            symbols_to_add = min(1, options.length - len(password))
            available_symbols = self._filter_characters(self.SYMBOL_CHARS, options)
            for _ in range(symbols_to_add):
                if available_symbols:
                    password += secrets.choice(available_symbols)
        
        return password
    
    def _build_character_set(self, options: GenerationOptions) -> str:
        """
        Build character set based on generation options
        
        Args:
            options (GenerationOptions): Generation configuration
            
        Returns:
            str: Available characters for password generation
        """
        charset = ""
        
        # Add character types based on options
        if options.include_lowercase:
            charset += self.LOWERCASE_CHARS
        
        if options.include_uppercase:
            charset += self.UPPERCASE_CHARS
        
        if options.include_digits:
            charset += self.DIGIT_CHARS
        
        if options.include_symbols:
            charset += self.SYMBOL_CHARS
        
        # Add custom characters
        if options.custom_characters:
            charset += options.custom_characters
        
        # Apply filtering
        charset = self._filter_characters(charset, options)
        
        # Remove duplicates while preserving order
        seen = set()
        filtered_charset = ""
        for char in charset:
            if char not in seen:
                seen.add(char)
                filtered_charset += char
        
        return filtered_charset
    
    def _filter_characters(self, charset: str, options: GenerationOptions) -> str:
        """
        Filter characters based on exclusion options
        
        Args:
            charset (str): Original character set
            options (GenerationOptions): Generation configuration
            
        Returns:
            str: Filtered character set
        """
        # Start with original charset
        filtered = charset
        
        # Remove similar characters if requested
        if options.exclude_similar:
            for char in self.SIMILAR_CHARS:
                filtered = filtered.replace(char, "")
        
        # Remove ambiguous characters if requested
        if options.exclude_ambiguous:
            for char in self.AMBIGUOUS_CHARS:
                filtered = filtered.replace(char, "")
        
        # Remove specifically excluded characters
        if options.excluded_characters:
            for char in options.excluded_characters:
                filtered = filtered.replace(char, "")
        
        return filtered
    
    def _generate_with_requirements(self, charset: str, options: GenerationOptions) -> str:
        """
        Generate password ensuring character type requirements are met
        
        Args:
            charset (str): Available characters
            options (GenerationOptions): Generation configuration
            
        Returns:
            str: Generated password meeting requirements
        """
        max_attempts = 100
        
        for attempt in range(max_attempts):
            # Generate random password
            password = ''.join(secrets.choice(charset) for _ in range(options.length))
            
            # Check if requirements are met
            if not options.require_each_type or self._meets_character_requirements(password, options):
                # Check for patterns if avoiding them
                if not options.avoid_patterns or not self._contains_patterns(password):
                    return password
        
        # If we can't generate a suitable password, force requirements
        return self._force_character_requirements(charset, options)
    
    def _meets_character_requirements(self, password: str, options: GenerationOptions) -> bool:
        """
        Check if password meets character type requirements
        
        Args:
            password (str): Password to check
            options (GenerationOptions): Requirements to check against
            
        Returns:
            bool: True if all requirements are met
        """
        if options.include_lowercase and not any(c.islower() for c in password):
            return False
        
        if options.include_uppercase and not any(c.isupper() for c in password):
            return False
        
        if options.include_digits and not any(c.isdigit() for c in password):
            return False
        
        if options.include_symbols:
            available_symbols = self._filter_characters(self.SYMBOL_CHARS, options)
            if available_symbols and not any(c in available_symbols for c in password):
                return False
        
        return True
    
    def _force_character_requirements(self, charset: str, options: GenerationOptions) -> str:
        """
        Generate password by forcing character type requirements
        
        Args:
            charset (str): Available characters
            options (GenerationOptions): Generation configuration
            
        Returns:
            str: Password meeting all requirements
        """
        password = []
        remaining_length = options.length
        
        # Add required character types first
        if options.include_lowercase and remaining_length > 0:
            password.append(secrets.choice(self.LOWERCASE_CHARS))
            remaining_length -= 1
        
        if options.include_uppercase and remaining_length > 0:
            password.append(secrets.choice(self.UPPERCASE_CHARS))
            remaining_length -= 1
        
        if options.include_digits and remaining_length > 0:
            password.append(secrets.choice(self.DIGIT_CHARS))
            remaining_length -= 1
        
        if options.include_symbols and remaining_length > 0:
            available_symbols = self._filter_characters(self.SYMBOL_CHARS, options)
            if available_symbols:
                password.append(secrets.choice(available_symbols))
                remaining_length -= 1
        
        # Fill remaining positions with random characters
        while remaining_length > 0:
            password.append(secrets.choice(charset))
            remaining_length -= 1
        
        # Shuffle to avoid predictable patterns
        for i in range(len(password)):
            j = secrets.randbelow(len(password))
            password[i], password[j] = password[j], password[i]
        
        return ''.join(password)
    
    def _contains_patterns(self, password: str) -> bool:
        """
        Check if password contains common patterns
        
        Args:
            password (str): Password to check
            
        Returns:
            bool: True if patterns are found
        """
        password_lower = password.lower()
        
        # Check keyboard patterns
        for pattern in self.KEYBOARD_PATTERNS:
            if pattern in password_lower:
                return True
        
        # Check for repeated characters
        if len(set(password)) < len(password) * 0.5:  # More than 50% repeated
            return True
        
        # Check for sequences
        for i in range(len(password) - 2):
            if len(password[i:i+3]) == 3:
                chars = password[i:i+3]
                if (ord(chars[1]) == ord(chars[0]) + 1 and 
                    ord(chars[2]) == ord(chars[1]) + 1):
                    return True
        
        return False
    
    def _analyze_password(self, password: str, options: GenerationOptions, 
                         method: str) -> GeneratedPassword:
        """
        Analyze generated password and provide metadata
        
        Args:
            password (str): Password to analyze
            options (GenerationOptions): Generation options used
            method (str): Generation method used
            
        Returns:
            GeneratedPassword: Password with analysis results
        """
        # Character type analysis
        character_types = {
            'lowercase': any(c.islower() for c in password),
            'uppercase': any(c.isupper() for c in password),
            'digits': any(c.isdigit() for c in password),
            'symbols': any(c in self.SYMBOL_CHARS for c in password)
        }
        
        # Calculate entropy (simplified)
        charset_size = 0
        if character_types['lowercase']:
            charset_size += 26
        if character_types['uppercase']:
            charset_size += 26
        if character_types['digits']:
            charset_size += 10
        if character_types['symbols']:
            charset_size += len(self.SYMBOL_CHARS)
        
        import math
        entropy = len(password) * math.log2(charset_size) if charset_size > 0 else 0
        
        # Strength scoring (0-100)
        strength_score = min(100, int(entropy * 2))  # Simplified scoring
        
        # Check requirements
        meets_requirements = self._meets_character_requirements(password, options)
        
        # Generate warnings and recommendations
        warnings = []
        recommendations = []
        
        if len(password) < 12:
            warnings.append("Password is shorter than recommended (12+ characters)")
            recommendations.append("Consider using a longer password")
        
        if not character_types['symbols']:
            recommendations.append("Consider including special characters")
        
        if self._contains_patterns(password):
            warnings.append("Password may contain predictable patterns")
            recommendations.append("Avoid keyboard patterns and sequences")
        
        return GeneratedPassword(
            password=password,
            strength_score=strength_score,
            entropy=entropy,
            character_types=character_types,
            generation_method=method,
            meets_requirements=meets_requirements,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def _load_word_list(self, word_list_path: Optional[str]) -> List[str]:
        """
        Load word list for memorable password generation
        
        Args:
            word_list_path (str, optional): Path to word list file
            
        Returns:
            List[str]: List of words for password generation
        """
        # Default word list for memorable passwords
        default_words = [
            "apple", "banana", "cherry", "dragon", "eagle", "forest", "guitar", "house",
            "island", "jungle", "knight", "lemon", "mountain", "ocean", "palace", "queen",
            "river", "sunset", "tiger", "umbrella", "valley", "winter", "yellow", "zebra",
            "adventure", "butterfly", "cascade", "diamond", "elephant", "fountain", "galaxy",
            "harmony", "infinity", "jasmine", "kaleidoscope", "lighthouse", "melody",
            "nightfall", "oasis", "phoenix", "quasar", "rainbow", "serenity", "thunder",
            "universe", "velocity", "whisper", "xenon", "yearning", "zephyr", "courage",
            "dream", "freedom", "hope", "joy", "peace", "strength", "wisdom", "energy",
            "magic", "mystery", "power", "spirit", "triumph", "victory", "wonder", "bliss"
        ]
        
        if word_list_path and Path(word_list_path).exists():
            try:
                with open(word_list_path, 'r', encoding='utf-8') as f:
                    words = [line.strip().lower() for line in f if line.strip()]
                
                # Filter words (4-8 characters, alphabetic only)
                filtered_words = [
                    word for word in words 
                    if 4 <= len(word) <= 8 and word.isalpha()
                ]
                
                if filtered_words:
                    logger.info(f"Loaded {len(filtered_words)} words from {word_list_path}")
                    return filtered_words
                else:
                    logger.warning(f"No suitable words found in {word_list_path}, using default")
            
            except Exception as e:
                logger.error(f"Failed to load word list from {word_list_path}: {e}")
        
        return default_words

# Utility functions for external use

def generate_random_password(length: int = 16, include_symbols: bool = True,
                           exclude_similar: bool = True) -> str:
    """
    Quick utility function to generate a random password
    
    Args:
        length (int): Password length
        include_symbols (bool): Include special characters
        exclude_similar (bool): Exclude confusing characters
        
    Returns:
        str: Generated password
    """
    options = GenerationOptions(
        length=length,
        include_symbols=include_symbols,
        exclude_similar=exclude_similar
    )
    
    generator = PasswordGenerator()
    result = generator.generate_password(options, GenerationMethod.RANDOM)
    return result.password

def generate_memorable_password(word_count: int = 4, separator: str = "-",
                               add_numbers: bool = True) -> str:
    """
    Quick utility function to generate a memorable password
    
    Args:
        word_count (int): Number of words to use
        separator (str): Word separator
        add_numbers (bool): Add numbers to the password
        
    Returns:
        str: Generated memorable password
    """
    options = GenerationOptions(
        word_count=word_count,
        word_separator=separator,
        add_numbers=add_numbers
    )
    
    generator = PasswordGenerator()
    result = generator.generate_password(options, GenerationMethod.MEMORABLE)
    return result.password

def analyze_password_strength(password: str) -> Dict[str, Any]:
    """
    Analyze password strength and provide recommendations
    
    Args:
        password (str): Password to analyze
        
    Returns:
        Dict[str, Any]: Analysis results
    """
    if not password:
        return {
            'strength_score': 0,
            'entropy': 0,
            'warnings': ['Password is empty'],
            'recommendations': ['Enter a password']
        }
    
    # Simple strength analysis
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    charset_size = 0
    if has_lower:
        charset_size += 26
    if has_upper:
        charset_size += 26
    if has_digit:
        charset_size += 10
    if has_symbol:
        charset_size += 32
    
    import math
    entropy = len(password) * math.log2(charset_size) if charset_size > 0 else 0
    strength_score = min(100, int(entropy * 2))
    
    warnings = []
    recommendations = []
    
    if len(password) < 8:
        warnings.append("Password is too short")
        recommendations.append("Use at least 8 characters")
    
    if not has_upper:
        recommendations.append("Add uppercase letters")
    
    if not has_digit:
        recommendations.append("Add numbers")
    
    if not has_symbol:
        recommendations.append("Add special characters")
    
    return {
        'strength_score': strength_score,
        'entropy': entropy,
        'character_types': {
            'lowercase': has_lower,
            'uppercase': has_upper,
            'digits': has_digit,
            'symbols': has_symbol
        },
        'warnings': warnings,
        'recommendations': recommendations
    }

if __name__ == "__main__":
    # Test code for password generation functionality
    print("Testing Personal Password Manager Password Generation...")
    
    try:
        # Create password generator
        generator = PasswordGenerator()
        
        # Test random password generation
        options = GenerationOptions(length=16, include_symbols=True)
        random_password = generator.generate_password(options, GenerationMethod.RANDOM)
        print(f"✓ Random password generated (strength: {random_password.strength_score})")
        print(f"  Length: {len(random_password.password)}, Entropy: {random_password.entropy:.1f} bits")
        
        # Test memorable password generation
        memorable_options = GenerationOptions(word_count=3, add_numbers=True)
        memorable_password = generator.generate_password(memorable_options, GenerationMethod.MEMORABLE)
        print(f"✓ Memorable password generated: {memorable_password.password}")
        
        # Test pattern-based generation
        pattern_options = GenerationOptions(pattern_template="Llll-dddd-Ssss")
        pattern_password = generator.generate_password(pattern_options, GenerationMethod.PATTERN)
        print(f"✓ Pattern password generated: {pattern_password.password}")
        
        # Test batch generation
        batch_passwords = generator.generate_batch(5, options, GenerationMethod.RANDOM)
        print(f"✓ Generated batch of {len(batch_passwords)} passwords")
        
        # Test utility functions
        quick_password = generate_random_password(12, True, True)
        print(f"✓ Quick random password: {len(quick_password)} characters")
        
        quick_memorable = generate_memorable_password(4, "-", True)
        print(f"✓ Quick memorable password: {quick_memorable}")
        
        # Test password analysis
        analysis = analyze_password_strength("TestPassword123!")
        print(f"✓ Password analysis score: {analysis['strength_score']}")
        
        print("✓ All password generation tests passed!")
        
    except Exception as e:
        print(f"❌ Password generation test failed: {e}")
        import traceback
        traceback.print_exc()