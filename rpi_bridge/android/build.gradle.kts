allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

subprojects {
    afterEvaluate {
        if (project.name == "flutter_bluetooth_serial") {
            val manifestFile = file("src/main/AndroidManifest.xml")
            if (manifestFile.exists()) {
                val content = manifestFile.readText()
                val cleaned = content.replace(
                    " package=\"io.github.edufolly.flutterbluetoothserial\"",
                    "",
                )
                if (content != cleaned) {
                    manifestFile.writeText(cleaned)
                }
            }
        }

        if (plugins.hasPlugin("com.android.library")) {
            extensions.getByType<com.android.build.gradle.LibraryExtension>().apply {
                if (namespace.isNullOrBlank()) {
                    namespace = if (project.name == "flutter_bluetooth_serial") {
                        "io.github.edufolly.flutterbluetoothserial"
                    } else {
                        "com.example.rpi_bridge.${project.name.replace('-', '_')}"
                    }
                }
            }
        }
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}

subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
