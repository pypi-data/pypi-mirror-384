from conan import ConanFile


class DeployConan(ConanFile):
    name = "${pkg.name}-deploy"
    version = "0.0.1"
    settings = "os", "compiler", "build_type", "arch"
    license = "Mulan PSL v2"
    requires = []

    def export(self):
        self.copy("manifest.yaml")

    def requirements(self):
        % for build_dep in dependencies:
        self.requires("${build_dep}")
        % endfor

    def build(self):
        pass

    def package(self):
        pass

    def package_info(self):
        pass
