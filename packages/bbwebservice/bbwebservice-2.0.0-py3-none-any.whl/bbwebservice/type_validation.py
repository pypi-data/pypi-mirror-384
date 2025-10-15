from typing import Type, Union, Optional, Literal, get_type_hints, List, Dict, Any
from types import FunctionType


class ValidationError:
    """Represents a single validation error found during schema checking."""
    def __init__(self, message: str, path: List[Union[str, int]], value: Any, expected_type: Any):
        self.message = message
        self.path = path if path is not None else []
        self.value = value
        self.expected_type = expected_type

    def __str__(self):
        path_str = ".".join(map(str, self.path)) if self.path else "root"
        return f"Validation Error at '{path_str}': {self.message}"

    def __repr__(self):
        return (f"ValidationError(message='{self.message}', path={self.path!r}, "
                f"value={self.value!r}, expected_type={self.expected_type!r})")

class MultipleValidationErrors(Exception):
    """
    Exception raised when multiple validation errors occur.
    Contains a list of ValidationError objects.
    """
    def __init__(self, errors: List[ValidationError]):
        self.errors = errors
        error_messages = "\n".join(str(err) for err in errors)
        super().__init__(f"Multiple validation errors occurred:\n{error_messages}")

# --- Metaklassen ---
class SchemeMeta(type):
    def __getitem__(cls, args):
        return cls(args)

class Scheme(type, metaclass=SchemeMeta):
    '''
    Der Scheme type erlaubt es, in einem definierten JSON Schema weitere JSON Schemata
    als Typ eines Attributs festzulegen.
    '''
    def __init__(self, schema: dict):
        self.schema = schema
        
    def __str__(self):
        return f'Schema: {str(self.schema)}'
    
    def __new__(cls,*args, **kwargs):
        klass = super().__new__(cls, "Scheme", (), {})
        return klass

class ConstraintMeta(type):
    def __getitem__(cls, args):
        if len(args) == 4:
            constraint_type, operator, value, error_message = args
        elif len(args) == 3:
            constraint_type, operator, value = args
            error_message = None
        else:
            raise TypeError("Constraint expects 3 or 4 arguments: (constraint_type, operator, value, [error_message])")
        return cls(constraint_type, operator, value, error_message)

class Constraint(type, metaclass= ConstraintMeta):
    '''
    Der Constraint type erlaubt es, in Typdeklarationen die Werte, die Typen annehmen können,
    einzuschränken.
    '''
    def __init__(self, constraint_type: Type, operator: str, value, error_message: Optional[str] = None):
        self.constraint_type = constraint_type
        self.operator = operator
        self.value = value
        self.error_message = error_message

    def is_satisfied(self, value):
        temp_errors = []
        if not satisfies(value, self.constraint_type, _errors=temp_errors):
            return False
        
        is_iterable = hasattr(value, '__len__') #and not isinstance(value, (str, bytes, bytearray))

        to_compare = len(value) if is_iterable else value

        if self.operator == 'f':
            return self.value(to_compare)
        
        if self.operator == '<':
            return to_compare < self.value
        elif self.operator == '<=':
            return to_compare <= self.value
        elif self.operator == '>':
            return to_compare > self.value
        elif self.operator == '>=':
            return to_compare >= self.value
        elif self.operator == '==':
            return to_compare == self.value
        elif self.operator == '!=':
            return to_compare != self.value
        else:
            return False
        
    def __str__(self):
        op_map = {
            '<': 'less than',
            '<=': 'less than or equal to',
            '>': 'greater than',
            '>=': 'greater than or equal to',
            '==': 'equal to',
            '!=': 'not equal to',
            'f': 'satisfies custom function'
        }
        operator_str = op_map.get(self.operator, f"'{self.operator}'")

        # Use _type_to_str for consistent deep representation of the constraint_type
        type_str = _type_to_str(self.constraint_type)

        if self.operator == 'f':
            s = f"type {type_str} that {operator_str}"
            if isinstance(self.value, FunctionType):
                s += f" ({self.value.__name__ if self.value.__name__ != '<lambda>' else 'lambda'})"
            else:
                s += f" ({self.value!r})"
        elif isinstance(self.value, type):
            s = f"type {type_str} {operator_str} {self.value.__name__}"
        else:
            s = f"type {type_str} {operator_str} {self.value!r}"

        if self.error_message:
            s += f" (Error: '{self.error_message}')"
        return f"Constraint[{s}]"

    def __repr__(self):
        if self.error_message:
            return f"Constraint[{self.constraint_type!r}, '{self.operator}', {self.value!r}, {self.error_message!r}]"
        return f"Constraint[{self.constraint_type!r}, '{self.operator}', {self.value!r}]"
    
    def __new__(cls,*args, **kwargs):
        klass = super().__new__(cls, "Constraint", (), {})
        return klass

# --- Hilfsfunktionen ---
def _type_to_str(type_hint) -> str:
    """
    Recursively converts a type hint to a human-readable string representation,
    handling custom Scheme and Constraint types gracefully.
    """
    if isinstance(type_hint, (Scheme, Constraint)):
        return str(type_hint)
    
    if hasattr(type_hint, "__origin__"):
        origin = type_hint.__origin__
        args = type_hint.__args__

        if origin is Union:
            return "Union[" + ", ".join(_type_to_str(arg) for arg in args) + "]"
        elif origin is list:
            return "List[" + _type_to_str(args[0]) + "]"
        elif origin is Optional:
            return "Optional[" + _type_to_str(args[0]) + "]"
        elif origin is dict:
            return "Dict[" + _type_to_str(args[0]) + ", " + _type_to_str(args[1]) + "]"
        elif origin is Literal:
            return "Literal[" + ", ".join(repr(arg) for arg in args) + "]"
        else:
            # Fallback for other typing generics
            return f"{origin.__name__}[{', '.join(_type_to_str(arg) for arg in args)}]"
    
    # Handle built-in types and Type objects
    if isinstance(type_hint, Type):
        if type_hint.__module__ == 'builtins':
            return type_hint.__name__
        return str(type_hint)
    elif type_hint is type(None): 
        return "None"
    
    return str(type_hint) 

def satisfies(value, form, strict=False, _errors: Optional[List[ValidationError]] = None, _path: Optional[List[Union[str, int]]] = None) -> bool:
    '''
    Die satisfies Funktion erlaubt es, Werte gegen Typdeklarationen zu prüfen.
    Sammelt Validierungsfehler in `_errors` statt sofort eine Exception zu werfen.
    Gibt True zurück, wenn der Wert das Formular erfüllt, False sonst.
    Fehler werden in die übergebene `_errors` Liste akkumuliert.
    '''
    if _errors is None:
        _errors = [] 
    if _path is None:
        _path = []

    if isinstance(form, Type) and not isinstance(form, (Constraint, Scheme)):
        is_satisfied = isinstance(value, form)
        if not is_satisfied:
            _errors.append(ValidationError(
                f"Value '{value!r}' of type '{type(value).__name__}' does not match expected type '{_type_to_str(form)}'.",
                _path, value, form
            ))
        return is_satisfied
    
    
    if isinstance(form, Constraint):
        is_satisfied = form.is_satisfied(value)
        if not is_satisfied:
            error_msg = f"Value '{value!r}' does not satisfy constraint '{_type_to_str(form)}'."
            if form.error_message:
                error_msg = form.error_message.format(arg_value=value, expected_type=_type_to_str(form))
            _errors.append(ValidationError(error_msg, _path, value, form))
        return is_satisfied
    

    if hasattr(form, "__origin__"):
        origin = form.__origin__
        args = form.__args__

        if origin is Union:
            union_branch_errors = []
            if any(satisfies(value, t, strict=strict, _errors=union_branch_errors, _path=_path) for t in args):
                return True 
            else:
                _errors.append(ValidationError(
                    f"Value '{value!r}' of type '{type(value).__name__}' does not satisfy any type in Union[{', '.join(_type_to_str(arg) for arg in args)}].",
                    _path, value, form
                ))
                return False
        elif origin is list:
            if not isinstance(value, list):
                _errors.append(ValidationError(
                    f"Expected list, got '{type(value).__name__}'.",
                    _path, value, form
                ))
                return False
            inner_type = args[0]
            if not value and (getattr(inner_type, '__origin__', None) is Optional or form is Optional[List[inner_type]]):
                return True

            all_items_satisfied = True
            for i, v in enumerate(value):
                if not satisfies(v, inner_type, strict=strict, _errors=_errors, _path=_path + [i]):
                    all_items_satisfied = False
            return all_items_satisfied
        elif origin is Optional:
            inner_type = args[0]
            if value is None:
                return True 
            return satisfies(value, inner_type, strict=strict, _errors=_errors, _path=_path)
        elif origin is dict:
            key_type, value_type = args
            if not isinstance(value, dict):
                _errors.append(ValidationError(
                    f"Expected dict, got '{type(value).__name__}'.",
                    _path, value, form
                ))
                return False
            all_kv_satisfied = True
            for k, v in value.items():
                if not satisfies(k, key_type, strict=strict, _errors=_errors, _path=_path + [f"key({k!r})"]):
                    all_kv_satisfied = False
                if not satisfies(v, value_type, strict=strict, _errors=_errors, _path=_path + [k]):
                    all_kv_satisfied = False
            return all_kv_satisfied
        elif origin is Literal:
            is_satisfied = value in args
            if not is_satisfied:
                _errors.append(ValidationError(
                    f"Value '{value!r}' is not one of the allowed literals: {', '.join(repr(arg) for arg in args)}.",
                    _path, value, form
                ))
            return is_satisfied
        else:
            _errors.append(ValidationError(
                f"Unsupported typing generic origin: '{origin.__name__}'.",
                _path, value, form
            ))
            return False 
    elif isinstance(form, Scheme):
        if not isinstance(value, dict):
            _errors.append(ValidationError(
                f"Expected dictionary for Scheme, got '{type(value).__name__}'.",
                _path, value, form
            ))
            return False
        original_error_count = len(_errors)
        validated_sub_instance = validate(value, form.schema, strict=strict, _errors=_errors, _path=_path)
        if len(_errors) > original_error_count:
            return False
        value.update(validated_sub_instance)
        return True

    elif form is type(None):
        is_satisfied = (value is None)
        if not is_satisfied:
            _errors.append(ValidationError(
                f"Expected None, got '{type(value).__name__}'.",
                _path, value, form
            ))
        return is_satisfied
    else:
        _errors.append(ValidationError(
            f"Unsupported type form or value: '{_type_to_str(form)}'.",
            _path, value, form
        ))
        return False

def validate(instance: dict, form: dict, strict: bool, _errors: Optional[List[ValidationError]] = None, _path: Optional[List[Union[str, int]]] = None) -> dict:
    '''
    Validiert eine Instanz (dict) gegen ein Schema (dict).
    Sammelt alle Validierungsfehler in `_errors` und gibt ein (partiell) validiertes Dictionary zurück.
    '''
    if _errors is None:
        _errors = []
    if _path is None:
        _path = []

    if not isinstance(instance, dict):
        _errors.append(ValidationError(f"Instance must be a dictionary, got {type(instance).__name__}.", _path, instance, dict))
        return {} 

    validated_instance = {}
    
    for key, schema_val in form.items():
        current_path = _path + [key]
        if not isinstance(schema_val, dict) or 'type' not in schema_val:
            continue 
        
        value = instance.get(key)
        field_type = schema_val['type']
        default = schema_val.get('default')

        key_is_present = key in instance

        if key_is_present:
            satisfies(value, field_type, strict=strict, _errors=_errors, _path=current_path)
            validated_instance[key] = value 
        elif default is not None:
            validated_instance[key] = default
        elif strict:
            if getattr(field_type, '__origin__', None) is not Optional:
                _errors.append(ValidationError(
                    f"Strict mode: Missing required field '{key}' and no default value provided.",
                    current_path, None, field_type
                ))
    if strict:
        for key in instance.keys():
            if key not in form:
                _errors.append(ValidationError(
                    f"Strict mode: Field '{key}' is not defined in the schema.",
                    _path + [key], instance[key], None 
                ))

    return validated_instance


def typed(func):
    '''
    Checks argument and return types at runtime.
    Raises MultipleValidationErrors if any checks fail, containing all found errors.
    '''
    def wrapper(*args, **kwargs):
        type_hints = get_type_hints(func)
        func_params = list(func.__code__.co_varnames[:func.__code__.co_argcount])
        
        bound_args = {}
        for i, arg_value in enumerate(args):
            if i < len(func_params):
                bound_args[func_params[i]] = arg_value
        bound_args.update(kwargs)

        all_errors: List[ValidationError] = []
        for arg_name, expected_type in type_hints.items():
            if arg_name == 'return':
                continue

            if arg_name in bound_args:
                arg_value = bound_args[arg_name]
                satisfies(arg_value, expected_type, _errors=all_errors, _path=[arg_name])
            elif arg_name in func_params and arg_name not in bound_args:
                if getattr(expected_type, '__origin__', None) is not Optional:
                    all_errors.append(ValidationError(
                        f"Missing required argument: '{arg_name}'.",
                        [arg_name], None, expected_type
                    ))
        if all_errors:
            raise MultipleValidationErrors(all_errors)
        result = func(*args, **kwargs)
        expected_return_type = type_hints.get('return')
        if expected_return_type is not None:
            satisfies(result, expected_return_type, _errors=all_errors, _path=["<return_value>"])
        if all_errors:
            raise MultipleValidationErrors(all_errors)
            
        return result
    
    return wrapper
