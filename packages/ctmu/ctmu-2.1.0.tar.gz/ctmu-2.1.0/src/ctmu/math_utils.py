"""Math and calculation utilities"""

import math
import statistics
import random

def calculate(expression):
    """Safe calculator"""
    try:
        # Only allow safe operations
        allowed = set('0123456789+-*/.() ')
        if not all(c in allowed for c in expression):
            return "Error: Invalid characters"
        
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

def convert_base(number, from_base, to_base):
    """Convert number between bases"""
    try:
        # Convert to decimal first
        if from_base == 10:
            decimal = int(number)
        elif from_base == 2:
            decimal = int(number, 2)
        elif from_base == 8:
            decimal = int(number, 8)
        elif from_base == 16:
            decimal = int(number, 16)
        else:
            return "Error: Unsupported base"
        
        # Convert from decimal to target base
        if to_base == 10:
            return str(decimal)
        elif to_base == 2:
            return bin(decimal)[2:]
        elif to_base == 8:
            return oct(decimal)[2:]
        elif to_base == 16:
            return hex(decimal)[2:].upper()
        else:
            return "Error: Unsupported base"
    except Exception as e:
        return f"Error: {e}"

def statistics_calc(numbers):
    """Calculate statistics for numbers"""
    try:
        nums = [float(x.strip()) for x in numbers.split(',')]
        return {
            'count': len(nums),
            'sum': sum(nums),
            'mean': statistics.mean(nums),
            'median': statistics.median(nums),
            'mode': statistics.mode(nums) if len(set(nums)) < len(nums) else 'No mode',
            'min': min(nums),
            'max': max(nums),
            'range': max(nums) - min(nums),
            'stdev': statistics.stdev(nums) if len(nums) > 1 else 0
        }
    except Exception as e:
        return f"Error: {e}"

def generate_random(type='int', min_val=1, max_val=100, count=1):
    """Generate random numbers"""
    try:
        results = []
        for _ in range(int(count)):
            if type == 'int':
                results.append(random.randint(int(min_val), int(max_val)))
            elif type == 'float':
                results.append(round(random.uniform(float(min_val), float(max_val)), 2))
        return results if len(results) > 1 else results[0]
    except Exception as e:
        return f"Error: {e}"

def unit_convert(value, from_unit, to_unit):
    """Convert between units"""
    try:
        value = float(value)
        
        # Length conversions (to meters)
        length_units = {
            'mm': 0.001, 'cm': 0.01, 'm': 1, 'km': 1000,
            'in': 0.0254, 'ft': 0.3048, 'yd': 0.9144, 'mi': 1609.34
        }
        
        # Weight conversions (to grams)
        weight_units = {
            'mg': 0.001, 'g': 1, 'kg': 1000,
            'oz': 28.3495, 'lb': 453.592
        }
        
        # Temperature conversions
        if from_unit == 'C' and to_unit == 'F':
            return (value * 9/5) + 32
        elif from_unit == 'F' and to_unit == 'C':
            return (value - 32) * 5/9
        elif from_unit == 'C' and to_unit == 'K':
            return value + 273.15
        elif from_unit == 'K' and to_unit == 'C':
            return value - 273.15
        
        # Length conversions
        if from_unit in length_units and to_unit in length_units:
            meters = value * length_units[from_unit]
            return meters / length_units[to_unit]
        
        # Weight conversions
        if from_unit in weight_units and to_unit in weight_units:
            grams = value * weight_units[from_unit]
            return grams / weight_units[to_unit]
        
        return "Error: Unsupported conversion"
    except Exception as e:
        return f"Error: {e}"