import inspect

from munch import Munch


class PropertyMunch(Munch):
    def __init__(self, instance, *args, **kwargs):
        """
        A Munch dictionary that dynamically exposes only @property attributes
        while keeping normal dictionary behavior for other keys.

        :param instance: The object whose properties will be dynamically accessible.
        """
        super().__init__(*args, **kwargs)
        self._instance = instance  # Store the actual object

        # Inject only properties (methods decorated with @property)
        for attr, value in inspect.getmembers(type(instance), lambda x: isinstance(x, property)):
            self._inject_property(attr)

    def _inject_property(self, attr):
        """
        Injects a @property as a dynamic property into the Munch dictionary.
        """
        prop = property(
            lambda self: getattr(self._instance, attr),  # Getter
            lambda self, value: (
                setattr(self._instance, attr, value)
                if hasattr(type(self._instance), attr) and getattr(type(self._instance), attr).fset
                else None
            ),  # Setter (if allowed)
        )
        setattr(self.__class__, attr, prop)  # Dynamically add the property


# Example usage
class Device:
    def __init__(self):
        self._cvendor = "Dell"
        self.model = "PowerEdge R740"  # Normal attribute, should NOT be exposed as a property

    @property
    def cvendor(self):
        return self._cvendor

    @cvendor.setter
    def cvendor(self, value):
        self._cvendor = value

    @property
    def serial_number(self):
        return "ABC123"  # Read-only property


device = Device()

# Create a PropertyMunch wrapping the Device instance
provides = Munch({"chassis_inventory": PropertyMunch(device)})

# ✅ Only @property attributes are accessible like properties
print(provides["chassis_inventory"].cvendor)  # Output: "Dell"
provides["chassis_inventory"].cvendor = "HP"
print(device.cvendor)  # Output: "HP"

print(provides["chassis_inventory"].serial_number)  # Output: "ABC123"
# provides["chassis_inventory"].serial_number = "XYZ789"  # ❌ Raises AttributeError (no setter)

# ❌ Normal attributes are NOT treated as properties
print(hasattr(provides["chassis_inventory"], "model"))  # Output: False
print("model" in provides["chassis_inventory"])  # Output: False

# ✅ Can still use Munch behavior for custom keys
provides["chassis_inventory"].custom_field = "Extra Data"
print(provides["chassis_inventory"].custom_field)  # Output: "Extra Data"
