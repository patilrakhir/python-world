
import json


# Step 1: Create our custom exception
class ConfigError(Exception):
    pass


# Step 2: Create the config loader function
def load_config(path):

    # Read the JSON file
    try:
        with open(path, "r", encoding="utf-8") as file:
            config = json.load(file)

    except FileNotFoundError as e:
        raise ConfigError(f"Config file not found: {path}") from e

    except json.JSONDecodeError as e:
        raise ConfigError("Invalid JSON format") from e

    # Step 3: Check required keys
    required_keys = ["db_host", "db_port", "timeout"]

    for key in required_keys:
        if key not in config:
            raise ConfigError(f"Missing required key: {key}")

    # Step 4: Validate db_port
    if type(config["db_port"]) is not int:
        raise ConfigError("db_port must be an integer")

    # Step 5: Return the configuration
    return config


# Step 6: Test the function
try:
    result = load_config("config.json")
    print("Configuration loaded successfully:")
    print(result)

except ConfigError as e:
    print("Configuration Error:", e)
