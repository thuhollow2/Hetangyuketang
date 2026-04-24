# Android APK build

This repository contains a minimal Android wrapper for the existing Python runner.
It uses Chaquopy to package the Python code into an APK and GitHub Actions to
build `app-debug.apk`.

## Build on GitHub

1. Push the repository to GitHub.
2. Open **Actions**.
3. Run **Build Android APK**.
4. Download the `yuketang-debug-apk` artifact from the completed workflow.

The workflow is defined in `.github/workflows/android-apk.yml`.

## Configuration

The APK intentionally packages `app/src/main/python/config.json`, which is an
empty template. The root `config.json` is not packaged because it may contain
private tokens and API keys.

On first launch, the app copies the template config to its private data
directory:

`/data/data/cn.yuketang.runner/files/yuketang/config.json`

Edit that file with your real settings before using the service. Cookie files,
downloaded QR codes and generated course files are also stored in this same
private directory.

## Local build

With JDK 17 and Gradle installed:

```sh
gradle :app:assembleDebug
```

On Windows, make sure `JAVA_HOME` points to JDK 17 or newer. For example:

```powershell
$env:JAVA_HOME = "C:\Program Files\Java\jdk-17"
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
.\gradlew.bat :app:assembleDebug
```

The APK will be created under:

`app/build/outputs/apk/debug/`

## Notes

- Minimum Android version is Android 7.0, API 24.
- The packaged ABIs are `arm64-v8a` and `x86_64`.
- The app starts the Python runner inside an Android foreground service.
