from labels.model.package import PackageType

JENKINS_PLUGIN_POM_PROPERTIES_GROUP_IDS = [
    "io.jenkins.plugins",
    "org.jenkins.plugins",
    "org.jenkins-ci.plugins",
    "io.jenkins-ci.plugins",
    "com.cloudbees.jenkins.plugins",
]


def get_java_package_type_from_group_id(group_id: str | None) -> PackageType:
    if any(
        group_id and group_id.startswith(prefix)
        for prefix in JENKINS_PLUGIN_POM_PROPERTIES_GROUP_IDS
    ) or (group_id and ".jenkins.plugin" in group_id):
        return PackageType.JenkinsPluginPkg
    return PackageType.JavaPkg
