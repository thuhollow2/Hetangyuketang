package cn.yuketang.runner;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;
import android.util.Log;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileWriter;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class YuketangService extends Service {
    public static final String ACTION_START = "cn.yuketang.runner.action.START";
    public static final String ACTION_STOP = "cn.yuketang.runner.action.STOP";
    private static final String CHANNEL_ID = "yuketang_runner";
    private static final int NOTIFICATION_ID = 1001;
    private Thread worker;
    private volatile boolean stopInProgress = false;

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String action = intent != null ? intent.getAction() : ACTION_START;
        if (ACTION_STOP.equals(action)) {
            requestStop();
            return START_NOT_STICKY;
        }
        stopInProgress = false;
        startForeground(NOTIFICATION_ID, buildNotification("Yuketang is running"));
        startPythonWorker();
        return START_NOT_STICKY;
    }

    @Override
    public void onDestroy() {
        worker = null;
        stopForeground(STOP_FOREGROUND_REMOVE);
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private synchronized void startPythonWorker() {
        if (stopInProgress) {
            return;
        }
        if (worker != null && worker.isAlive()) {
            return;
        }
        worker = new Thread(() -> {
            try {
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(this));
                }
                PyObject module = Python.getInstance().getModule("android_entry");
                module.callAttr("start", getFilesDir().getAbsolutePath());
            } catch (Exception e) {
                Log.e("YuketangService", "Python runner crashed", e);
                writeRuntimeError(e);
                startForeground(NOTIFICATION_ID, buildNotification("Yuketang crashed. Check logs."));
            }
        }, "YuketangPython");
        worker.start();
    }

    private synchronized void requestStop() {
        if (stopInProgress) {
            return;
        }
        stopInProgress = true;
        writeServiceStatus("stopping", "Stop requested");
        new Thread(() -> {
            requestPythonStop();
            writeServiceStatus("stopped", "Runner stopped");
            stopForeground(STOP_FOREGROUND_REMOVE);
            stopSelf();
            android.os.Process.killProcess(android.os.Process.myPid());
        }, "YuketangStop").start();
    }

    private void requestPythonStop() {
        try {
            if (Python.isStarted()) {
                Python.getInstance().getModule("android_entry").callAttr("stop");
            }
        } catch (Exception e) {
            Log.e("YuketangService", "Failed to stop Python runner", e);
        } finally {
            worker = null;
        }
    }

    private Notification buildNotification(String text) {
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID, "Yuketang Runner", NotificationManager.IMPORTANCE_LOW);
            manager.createNotificationChannel(channel);
        }

        Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, CHANNEL_ID)
                : new Notification.Builder(this);
        return builder
                .setContentTitle("Yuketang")
                .setContentText(text)
                .setSmallIcon(android.R.drawable.stat_notify_sync)
                .setOngoing(true)
                .build();
    }

    private void writeRuntimeError(Exception e) {
        try {
            File home = new File(getFilesDir(), "yuketang");
            if (!home.exists()) {
                home.mkdirs();
            }
            File statusFile = new File(home, "status.json");
            JSONObject status = new JSONObject();
            status.put("state", "error");
            status.put("message", e.getClass().getSimpleName() + ": " + (e.getMessage() != null ? e.getMessage() : ""));
            status.put("last_tick", new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss", java.util.Locale.US).format(new java.util.Date()));
            try (FileWriter writer = new FileWriter(statusFile, false)) {
                writer.write(status.toString(2));
            }
            File logFile = new File(home, "runner.log");
            try (FileWriter writer = new FileWriter(logFile, true)) {
                writer.write("[Java] " + e.toString() + "\n");
            }
        } catch (Exception ignored) {
        }
    }

    private void writeServiceStatus(String state, String message) {
        try {
            File home = new File(getFilesDir(), "yuketang");
            if (!home.exists()) {
                home.mkdirs();
            }
            File statusFile = new File(home, "status.json");
            JSONObject status = new JSONObject();
            if (statusFile.exists()) {
                try {
                    byte[] bytes = new byte[(int) statusFile.length()];
                    try (FileInputStream input = new FileInputStream(statusFile)) {
                        int read = input.read(bytes);
                        if (read > 0) {
                            status = new JSONObject(new String(bytes, 0, read));
                        }
                    }
                } catch (Exception ignored) {
                    status = new JSONObject();
                }
            }
            status.put("state", state);
            status.put("message", message);
            status.put("last_tick", new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US).format(new Date()));
            try (FileWriter writer = new FileWriter(statusFile, false)) {
                writer.write(status.toString(2));
            }
        } catch (Exception ignored) {
        }
    }
}
