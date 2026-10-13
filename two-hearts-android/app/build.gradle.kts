plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.raeeq.link"
    compileSdk = 35

    signingConfigs {
        create("linkDebug") {
            storeFile = rootProject.file("link-debug.keystore")
            storePassword = "android"
            keyAlias = "linkdebug"
            keyPassword = "android"
            storeType = "JKS"
        }
    }

    defaultConfig {
        applicationId = "com.raeeq.link"
        minSdk = 31
        targetSdk = 34
        versionCode = 3
        versionName = "0.3.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        getByName("debug") {
            signingConfig = signingConfigs.getByName("linkDebug")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    implementation("androidx.activity:activity:1.9.3")
    implementation("com.journeyapps:zxing-android-embedded:4.3.0")
    testImplementation("junit:junit:4.13.2")
}
