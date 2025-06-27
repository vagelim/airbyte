import hashlib
import re
from typing import Any

from .base import BaseGenerator


class EmailMaskingGenerator(BaseGenerator):
    """
    Generator for masking email addresses while preserving domain structure.
    
    Transforms emails like "john.doe@company.com" to "****@company.com"
    or generates consistent fake emails based on the original.
    """
    
    def generate(self, value: Any) -> str:
        """
        Generate a masked email address.
        
        Args:
            value: Original email address
            
        Returns:
            Masked email address
        """
        if not isinstance(value, str) or not self._is_valid_email(value):
            return str(value)
        
        local_part, domain_part = value.split('@', 1)
        
        mask_type = self.config.get('mask_type', 'asterisk')
        preserve_domain = self.config.get('preserve_domain', True)
        
        if mask_type == 'asterisk':
            masked_local = '*' * len(local_part)
        elif mask_type == 'hash':
            hash_input = f"{self.seed}:{value}"
            hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:8]
            masked_local = f"user{hash_value}"
        else:
            masked_local = '*' * len(local_part)
        
        if preserve_domain:
            return f"{masked_local}@{domain_part}"
        else:
            return f"{masked_local}@example.com"
    
    def _is_valid_email(self, email: str) -> bool:
        """Check if the string is a valid email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


class PhoneMaskingGenerator(BaseGenerator):
    """
    Generator for masking phone numbers while preserving format structure.
    
    Transforms phone numbers like "(555) 123-4567" to "(***) ***-4567"
    """
    
    def generate(self, value: Any) -> str:
        """
        Generate a masked phone number.
        
        Args:
            value: Original phone number
            
        Returns:
            Masked phone number
        """
        if not isinstance(value, str):
            return str(value)
        
        digits_only = re.sub(r'\D', '', value)
        
        if len(digits_only) < 7:
            return '*' * len(value)
        
        preserve_last_digits = self.config.get('preserve_last_digits', 4)
        mask_char = self.config.get('mask_char', '*')
        
        result = value
        digit_positions = []
        
        for i, char in enumerate(value):
            if char.isdigit():
                digit_positions.append(i)
        
        digits_to_preserve = min(preserve_last_digits, len(digit_positions))
        digits_to_mask = len(digit_positions) - digits_to_preserve
        
        result_chars = list(result)
        for i in range(digits_to_mask):
            pos = digit_positions[i]
            result_chars[pos] = mask_char
        
        return ''.join(result_chars)


class SSNMaskingGenerator(BaseGenerator):
    """
    Generator for masking Social Security Numbers.
    
    Transforms SSNs like "123-45-6789" to "***-**-6789"
    """
    
    def generate(self, value: Any) -> str:
        """
        Generate a masked SSN.
        
        Args:
            value: Original SSN
            
        Returns:
            Masked SSN
        """
        if not isinstance(value, str):
            return str(value)
        
        digits_only = re.sub(r'\D', '', value)
        
        if len(digits_only) != 9:
            return '*' * len(value)
        
        preserve_last_digits = self.config.get('preserve_last_digits', 4)
        mask_char = self.config.get('mask_char', '*')
        
        if '-' in value:
            parts = value.split('-')
            if len(parts) == 3:
                if preserve_last_digits >= 4:
                    return f"***-**-{parts[2]}"
                elif preserve_last_digits >= 2:
                    return f"***-**-**{parts[2][-2:]}"
                else:
                    return "***-**-****"
        elif ' ' in value:
            parts = value.split(' ')
            if len(parts) == 3:
                if preserve_last_digits >= 4:
                    return f"*** ** {parts[2]}"
                elif preserve_last_digits >= 2:
                    return f"*** ** **{parts[2][-2:]}"
                else:
                    return "*** ** ****"
        else:
            if preserve_last_digits >= 4:
                return f"*****{digits_only[-4:]}"
            elif preserve_last_digits >= 2:
                return f"*******{digits_only[-2:]}"
            else:
                return "*********"
        
        return '*' * len(value)
