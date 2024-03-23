import os
import yaml
import importlib.util


class PluginManager:
    def __init__(self, app, plugins_path="plugins/"):
        self.app = app
        self.plugins_path = plugins_path
        self.plugins = []

    def load_plugins(self):
        for item in os.listdir(self.plugins_path):
            plugin_dir = os.path.join(self.plugins_path, item)
            if os.path.isdir(plugin_dir):
                self.load_plugin(plugin_dir)

    def load_plugin(self, plugin_dir):
        config_path = os.path.join(plugin_dir, "plugin.yml")
        if os.path.exists(config_path):
            with open(config_path, "r") as file:
                try:
                    plugin_config = yaml.safe_load(file)
                    # Check if plugin_config is None or if it's missing essential keys
                    if plugin_config is None or "name" not in plugin_config:
                        self.app.log.warning(
                            f"Skipping plugin at {plugin_dir}: 'plugin.yml' is empty or invalid."
                        )
                        return
                except yaml.YAMLError as e:
                    self.app.log.error(
                        f"Error loading 'plugin.yml' from {plugin_dir}: {e}"
                    )
                    return  # Skip this plugin due to error

                self.app.log.info(f"Loading plugin: {plugin_config['name']}")
                self.import_plugin_module(plugin_dir, plugin_config)

    def import_plugin_module(self, plugin_dir, plugin_config):
        main_module_path = os.path.join(plugin_dir, f"{plugin_config['name']}.py")
        if os.path.exists(main_module_path):
            module_name = f"plugins.{plugin_config['name']}"
            spec = importlib.util.spec_from_file_location(module_name, main_module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "Plugin"):
                plugin_instance = module.Plugin(self.app, plugin_config)
                self.plugins.append(
                    {"instance": plugin_instance, "config": plugin_config}
                )

    def get_plugins_info(self):
        plugins_info = []  # Initialize an empty list to hold plugin information.
        for entry in self.plugins:
            config = entry["config"]
            plugin_info = {
                "name": config["name"],
                "version": config.get("version", "Unknown"),
                "author": config.get("author", "Unknown"),
                "description": config.get("description", "No description provided"),
                "github": config.get("github", "Not provided"),
            }
            plugins_info.append(plugin_info)  # Add the dictionary to the list.
        return plugins_info  # Return the list of dictionaries.
