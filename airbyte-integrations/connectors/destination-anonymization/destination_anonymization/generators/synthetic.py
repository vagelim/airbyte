import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional

from faker import Faker

from .base import BaseGenerator


class FakeNameGenerator(BaseGenerator):
    """
    Generator for creating realistic fake names using Faker library.
    
    Supports generating first names, last names, or full names
    with consistent output based on seed.
    """
    
    def __init__(self, seed: str = "default", **config):
        super().__init__(seed, **config)
        seed_hash = int(hashlib.md5(f"{seed}:name".encode()).hexdigest()[:8], 16)
        self.faker = Faker()
        Faker.seed(seed_hash)
    
    def generate(self, value: Any) -> str:
        """
        Generate a fake name.
        
        Args:
            value: Original name value (used for consistency)
            
        Returns:
            Generated fake name
        """
        name_type = self.config.get('name_type', 'full_name')
        gender = self.config.get('gender', None)
        
        value_seed = int(hashlib.md5(f"{self.seed}:{value}".encode()).hexdigest()[:8], 16)
        self.faker.seed(value_seed)
        
        if name_type == 'first_name':
            if gender == 'male':
                return self.faker.first_name_male()
            elif gender == 'female':
                return self.faker.first_name_female()
            else:
                return self.faker.first_name()
        elif name_type == 'last_name':
            return self.faker.last_name()
        elif name_type == 'full_name':
            if gender == 'male':
                return self.faker.name_male()
            elif gender == 'female':
                return self.faker.name_female()
            else:
                return self.faker.name()
        else:
            return self.faker.name()


class FakeAddressGenerator(BaseGenerator):
    """
    Generator for creating realistic fake addresses using Faker library.
    
    Supports generating various address components with consistent output.
    """
    
    def __init__(self, seed: str = "default", **config):
        super().__init__(seed, **config)
        seed_hash = int(hashlib.md5(f"{seed}:address".encode()).hexdigest()[:8], 16)
        self.faker = Faker()
        Faker.seed(seed_hash)
    
    def generate(self, value: Any) -> str:
        """
        Generate a fake address.
        
        Args:
            value: Original address value (used for consistency)
            
        Returns:
            Generated fake address
        """
        address_type = self.config.get('address_type', 'full_address')
        country = self.config.get('country', 'US')
        
        value_seed = int(hashlib.md5(f"{self.seed}:{value}".encode()).hexdigest()[:8], 16)
        self.faker.seed(value_seed)
        
        if country != 'US':
            try:
                self.faker = Faker(country.lower())
                self.faker.seed(value_seed)
            except:
                pass
        
        if address_type == 'street_address':
            return self.faker.street_address()
        elif address_type == 'city':
            return self.faker.city()
        elif address_type == 'state':
            return self.faker.state()
        elif address_type == 'zipcode':
            return self.faker.zipcode()
        elif address_type == 'country':
            return self.faker.country()
        elif address_type == 'full_address':
            return self.faker.address().replace('\n', ', ')
        else:
            return self.faker.address().replace('\n', ', ')


class FakeDateGenerator(BaseGenerator):
    """
    Generator for creating realistic fake dates while preserving date patterns.
    
    Maintains relative date relationships and generates dates within
    specified ranges.
    """
    
    def __init__(self, seed: str = "default", **config):
        super().__init__(seed, **config)
        seed_hash = int(hashlib.md5(f"{seed}:date".encode()).hexdigest()[:8], 16)
        self.faker = Faker()
        Faker.seed(seed_hash)
    
    def generate(self, value: Any) -> str:
        """
        Generate a fake date.
        
        Args:
            value: Original date value
            
        Returns:
            Generated fake date in the same format
        """
        if not value:
            return value
        
        original_date = self._parse_date(value)
        if not original_date:
            return self._generate_random_date()
        
        value_seed = int(hashlib.md5(f"{self.seed}:{value}".encode()).hexdigest()[:8], 16)
        self.faker.seed(value_seed)
        
        start_date = self.config.get('start_date', '1950-01-01')
        end_date = self.config.get('end_date', '2023-12-31')
        preserve_format = self.config.get('preserve_format', True)
        
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            fake_date = self.faker.date_between(start_date=start_dt, end_date=end_dt)
            
            if preserve_format:
                return self._format_date_like_original(datetime.combine(fake_date, datetime.min.time()), str(value))
            else:
                return fake_date.strftime('%Y-%m-%d')
                
        except Exception:
            return self._generate_random_date()
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Try to parse a date string using common formats.
        
        Args:
            date_str: Date string to parse
            
        Returns:
            Parsed datetime object or None
        """
        common_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
        ]
        
        for fmt in common_formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue
        
        return None
    
    def _format_date_like_original(self, fake_date: datetime, original: str) -> str:
        """
        Format the fake date to match the original format.
        
        Args:
            fake_date: Generated fake date
            original: Original date string
            
        Returns:
            Formatted date string
        """
        if '/' in original:
            if original.index('/') < 3:  # MM/DD/YYYY or DD/MM/YYYY
                return fake_date.strftime('%m/%d/%Y')
            else:
                return fake_date.strftime('%Y/%m/%d')
        elif 'T' in original:
            if original.endswith('Z'):
                return fake_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            else:
                return fake_date.strftime('%Y-%m-%dT%H:%M:%S')
        elif ' ' in original and ':' in original:
            return fake_date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return fake_date.strftime('%Y-%m-%d')
    
    def _generate_random_date(self) -> str:
        """Generate a random date as fallback."""
        return self.faker.date_between(
            start_date=datetime(1950, 1, 1),
            end_date=datetime(2023, 12, 31)
        ).strftime('%Y-%m-%d')
