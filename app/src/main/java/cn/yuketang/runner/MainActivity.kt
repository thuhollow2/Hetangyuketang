package cn.yuketang.runner

import android.Manifest
import android.content.ClipData
import android.content.ClipboardManager
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.BitmapFactory
import android.net.Uri
import android.app.TimePickerDialog
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Download
import androidx.compose.material.icons.outlined.Edit
import androidx.compose.material.icons.outlined.Share
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshots.SnapshotStateList
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlinx.coroutines.delay
import androidx.core.content.FileProvider

private val Background = Color(0xFFF5F7FB)
private val Ink = Color(0xFF16202A)
private val Muted = Color(0xFF64748B)
private val Primary = Color(0xFF0F766E)
private val Accent = Color(0xFF4F46E5)
private val WEEK_DAYS = linkedMapOf(
    "1" to "周一",
    "2" to "周二",
    "3" to "周三",
    "4" to "周四",
    "5" to "周五",
    "6" to "周六",
    "7" to "周日",
)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        ensureNotificationPermission()
        ensureHome()
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize(), color = Background) {
                    RunnerApp(
                        homeDir = homeDir(),
                        onStart = { startRunner() },
                        onStop = { stopRunner() },
                    )
                }
            }
        }
    }

    private fun ensureNotificationPermission() {
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1)
        }
    }

    private fun startRunner() {
        val configFile = File(homeDir(), "config.json")
        if (countEnabledUsers(configFile) == 0) {
            toast("没有启用账号，请先在配置里启用至少一个账号")
            return
        }
        try {
            val intent = Intent(this, YuketangService::class.java).apply {
                action = YuketangService.ACTION_START
            }
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(intent) else startService(intent)
            toast("已请求启动服务")
        } catch (e: Exception) {
            toast("启动失败：${e.message ?: "未知错误"}")
        }
    }

    private fun stopRunner() {
        try {
            val intent = Intent(this, YuketangService::class.java).apply {
                action = YuketangService.ACTION_STOP
            }
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(intent) else startService(intent)
            toast("已请求停止服务")
        } catch (e: Exception) {
            try {
                stopService(Intent(this, YuketangService::class.java))
            } catch (_: Exception) {
            }
            toast("停止失败：${e.message ?: "未知错误"}")
        }
    }

    private fun ensureHome() {
        val home = homeDir()
        if (!home.exists()) home.mkdirs()
        runtimeDataDir(home).mkdirs()
        val config = File(home, "config.json")
        if (!config.exists()) config.writeText(DEFAULT_CONFIG, Charsets.UTF_8)
        organizeRuntimeFiles(home)
    }

    private fun homeDir() = File(filesDir, "yuketang")

    private fun toast(text: String) {
        Toast.makeText(this, text, Toast.LENGTH_SHORT).show()
    }
}

private enum class Tab(val label: String) {
    Home("首页"),
    Config("配置"),
    Logs("日志"),
    Files("文件"),
}

private enum class ConfigTab(val label: String) {
    Users("账号"),
    Services("通知"),
    Models("模型"),
    Global("全局"),
    Json("JSON"),
}

@Composable
private fun RunnerApp(homeDir: File, onStart: () -> Unit, onStop: () -> Unit) {
    var selectedTab by remember { mutableStateOf(Tab.Home) }

    Column(modifier = Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(Color.White)
                .statusBarsPadding()
                .padding(start = 20.dp, top = 8.dp, end = 20.dp, bottom = 14.dp),
        ) {
            Text("雨课堂助手", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Ink)
            Text("后台运行、扫码登录、配置管理", fontSize = 13.sp, color = Muted)
        }

        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(16.dp),
        ) {
            when (selectedTab) {
                Tab.Home -> HomeScreen(homeDir, onStart, onStop, onEditConfig = { selectedTab = Tab.Config })
                Tab.Config -> ConfigScreen(homeDir)
                Tab.Logs -> LogsScreen(homeDir)
                Tab.Files -> FilesScreen(homeDir)
            }
        }

        NavigationBar(
            modifier = Modifier.navigationBarsPadding(),
            containerColor = Color.White,
            tonalElevation = 0.dp,
        ) {
            Tab.entries.forEach { tab ->
                NavigationBarItem(
                    selected = tab == selectedTab,
                    onClick = { selectedTab = tab },
                    label = { Text(tab.label) },
                    icon = { Text(tab.label.take(1), fontWeight = FontWeight.Bold) },
                )
            }
        }
    }
}

@Composable
private fun HomeScreen(homeDir: File, onStart: () -> Unit, onStop: () -> Unit, onEditConfig: () -> Unit) {
    var status by remember { mutableStateOf(JSONObject()) }
    var qrRefreshTick by remember { mutableStateOf(0L) }

    LaunchedEffect(homeDir) {
        while (true) {
            organizeRuntimeFiles(homeDir)
            status = readJson(File(homeDir, "status.json"))
            qrRefreshTick = System.currentTimeMillis()
            delay(2000)
        }
    }

    val configFile = File(homeDir, "config.json")
    val state = status.optString("state", "stopped")
    val enabledUsers = status.optInt("enabled_users", countEnabledUsers(configFile))
    val pendingQrFiles = remember(qrRefreshTick, fileTime(configFile)) { pendingQrFiles(homeDir) }
    val starting = state == "starting"
    val running = state == "running"
    val stopping = state == "stopping"
    val startEnabled = !running && !starting && !stopping
    val stopEnabled = running || starting

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        CardBlock {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(modifier = Modifier.weight(1f)) {
                    Text("服务状态", color = Muted, fontSize = 13.sp)
                    Text(stateLabel(state), color = statusColor(state), fontSize = 28.sp, fontWeight = FontWeight.Bold)
                }
            }
            Spacer(Modifier.height(14.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                MetricCard("启用账号", enabledUsers.toString(), Modifier.weight(1f))
                MetricCard("配置更新时间", fileTime(configFile).takeLast(8), Modifier.weight(1f))
            }
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                MetricCard("最近心跳", status.optString("last_tick", "-").takeLast(8), Modifier.weight(1f))
                MetricCard("待扫码", pendingQrFiles.size.toString(), Modifier.weight(1f))
            }
        }

        if (pendingQrFiles.isNotEmpty()) {
            CardBlock {
                Text("待扫码提醒", fontWeight = FontWeight.Bold, color = Ink)
                Spacer(Modifier.height(8.dp))
                Text(
                    pendingQrFiles.joinToString("、") { qrOwnerName(it) },
                    color = Color(0xFF334155),
                    fontSize = 14.sp,
                )
            }
        }

        CardBlock {
            Text("运行信息", fontWeight = FontWeight.Bold, color = Ink)
            Spacer(Modifier.height(8.dp))
            InfoRow("启动时间", status.optString("started_at", "-"))
            InfoRow("最近消息", status.optString("message", "-"))
        }

        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Button(
                onClick = onStart,
                enabled = startEnabled,
                modifier = Modifier.weight(1f).height(48.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Primary),
            ) {
                Text("启动服务")
            }
            OutlinedButton(
                onClick = onStop,
                enabled = stopEnabled,
                modifier = Modifier.weight(1f).height(48.dp),
            ) {
                Text("停止服务")
            }
        }
        OutlinedButton(onClick = onEditConfig, modifier = Modifier.fillMaxWidth().height(46.dp)) {
            Text("进入配置管理")
        }
    }
}

@Composable
private fun ConfigScreen(homeDir: File) {
    val configFile = File(homeDir, "config.json")
    var selected by remember { mutableStateOf(ConfigTab.Users) }
    var configText by remember { mutableStateOf(readText(configFile, DEFAULT_CONFIG)) }
    var message by remember { mutableStateOf("") }
    val config = remember(configText) { runCatching { JSONObject(configText) }.getOrElse { JSONObject(DEFAULT_CONFIG) } }

    fun reload() {
        configText = readText(configFile, DEFAULT_CONFIG)
    }

    fun saveConfig(next: JSONObject, ok: String) {
        ensureConfigDefaults(next)
        configFile.parentFile?.mkdirs()
        configFile.writeText(next.toString(2) + "\n", Charsets.UTF_8)
        configText = next.toString(2)
        message = ok
    }

    Column(modifier = Modifier.fillMaxSize()) {
        Row(
            modifier = Modifier.horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            ConfigTab.entries.forEach { tab ->
                val active = tab == selected
                if (active) {
                    Button(onClick = { selected = tab }, colors = ButtonDefaults.buttonColors(containerColor = Primary)) {
                        Text(tab.label)
                    }
                } else {
                    OutlinedButton(onClick = { selected = tab }) {
                        Text(tab.label)
                    }
                }
            }
        }
        if (message.isNotBlank()) {
            Text(message, color = Primary, fontSize = 13.sp, modifier = Modifier.padding(top = 8.dp))
        }
        Spacer(Modifier.height(12.dp))

        when (selected) {
            ConfigTab.Users -> UsersConfig(homeDir, config, ::saveConfig, { message = it })
            ConfigTab.Services -> ServicesConfig(homeDir, config, ::saveConfig, { message = it })
            ConfigTab.Models -> ModelsConfig(config, ::saveConfig, { message = it })
            ConfigTab.Global -> GlobalConfig(config, ::saveConfig)
            ConfigTab.Json -> JsonConfig(configFile, configText, { configText = it }, { reload() }, { message = it })
        }
    }
}

@Composable
private fun UsersConfig(
    homeDir: File,
    config: JSONObject,
    save: (JSONObject, String) -> Unit,
    onMessage: (String) -> Unit,
) {
    var dialogState by remember { mutableStateOf<UserDialogState?>(null) }
    var qrPreview by remember { mutableStateOf<String?>(null) }
    var qrRefreshTick by remember { mutableStateOf(0L) }
    val users = config.optJSONObject("yuketang")?.optJSONArray("users") ?: JSONArray()
    val serviceNames = config.optJSONObject("send")
        ?.optJSONArray("services")
        ?.let { services ->
            buildList {
                for (i in 0 until services.length()) {
                    services.optJSONObject(i)?.optString("name")?.takeIf { it.isNotBlank() }?.let(::add)
                }
            }
        }
        ?: emptyList()

    LaunchedEffect(homeDir) {
        while (true) {
            organizeRuntimeFiles(homeDir)
            qrRefreshTick = System.currentTimeMillis()
            delay(2000)
        }
    }

    ConfigList(
        title = "账号配置",
        action = "新增账号",
        onAction = { dialogState = UserDialogState(index = null, user = null) },
    ) {
        if (users.length() == 0) EmptyHint("还没有账号，新增后再启动服务")
        for (i in 0 until users.length()) {
            val user = users.optJSONObject(i) ?: continue
            val qrFile = remember(qrRefreshTick, user.optString("name")) { qrCodeFileForName(homeDir, user.optString("name")) }
            AccountConfigItem(
                title = user.optString("name", "未命名账号"),
                subtitle = buildUserSubtitle(user),
                detail = buildUserDetail(user),
                qrFile = qrFile,
                onClick = { dialogState = UserDialogState(index = i, user = JSONObject(user.toString())) },
                onQrClick = { qrPreview = user.optString("name") },
            )
        }
    }

    dialogState?.let { state ->
        UserDialog(
            serviceNames = serviceNames,
            initialUser = state.user,
            onDismiss = { dialogState = null },
            onConfirm = { user ->
                val next = JSONObject(config.toString())
                val array = next.getJSONObject("yuketang").getJSONArray("users")
                val name = user.optString("name")
                if (hasDuplicateName(array, name, state.index)) {
                    onMessage("账号名称不能重复")
                    return@UserDialog
                }
                if (state.index == null) {
                    array.put(user)
                    save(next, "账号已新增")
                } else {
                    state.user?.optString("name")?.takeIf { it != name }?.let { deleteUserCookieFiles(homeDir, it) }
                    array.put(state.index, user)
                    save(next, "账号已保存")
                }
                dialogState = null
            },
            onDelete = if (state.index == null) null else {
                {
                    state.user?.optString("name")?.let { deleteUserCookieFiles(homeDir, it) }
                    val next = JSONObject(config.toString())
                    val src = next.getJSONObject("yuketang").getJSONArray("users")
                    val dst = JSONArray()
                    for (i in 0 until src.length()) {
                        if (i != state.index) dst.put(src.get(i))
                    }
                    next.getJSONObject("yuketang").put("users", dst)
                    save(next, "账号已删除")
                    dialogState = null
                }
            },
        )
    }
    qrPreview?.let { name ->
        QrPreviewDialog(
            file = qrCodeFileForName(homeDir, name),
            title = name,
            onDismiss = { qrPreview = null },
        )
    }
}

@Composable
private fun ServicesConfig(
    homeDir: File,
    config: JSONObject,
    save: (JSONObject, String) -> Unit,
    onMessage: (String) -> Unit,
) {
    var dialogState by remember { mutableStateOf<ServiceDialogState?>(null) }
    val services = config.optJSONObject("send")?.optJSONArray("services") ?: JSONArray()

    ConfigList("通知服务", "新增通知", { dialogState = ServiceDialogState(null, null) }) {
        if (services.length() == 0) EmptyHint("还没有通知服务")
        for (i in 0 until services.length()) {
            val item = services.optJSONObject(i) ?: continue
            ConfigItem(
                title = item.optString("name", "未命名服务"),
                subtitle = buildServiceSubtitle(item),
                detail = buildServiceDetail(item),
                onClick = { dialogState = ServiceDialogState(i, JSONObject(item.toString())) },
            )
        }
    }

    dialogState?.let { state ->
        ServiceDialog(
            initialService = state.service,
            onDismiss = { dialogState = null },
            onConfirm = { service ->
                val next = JSONObject(config.toString())
                val array = next.getJSONObject("send").getJSONArray("services")
                val name = service.optString("name")
                if (hasDuplicateName(array, name, state.index)) {
                    onMessage("通知名称不能重复")
                    return@ServiceDialog
                }
                if (state.index == null) {
                    array.put(service)
                    save(next, "通知服务已新增")
                } else {
                    state.service?.optString("name")?.takeIf { it != name }?.let { deleteServiceTokenFiles(homeDir, it) }
                    array.put(state.index, service)
                    save(next, "通知服务已保存")
                }
                dialogState = null
            },
            onDelete = if (state.index == null) null else {
                {
                    state.service?.optString("name")?.let { deleteServiceTokenFiles(homeDir, it) }
                    val next = JSONObject(config.toString())
                    val src = next.getJSONObject("send").getJSONArray("services")
                    val dst = JSONArray()
                    for (i in 0 until src.length()) if (i != state.index) dst.put(src.get(i))
                    next.getJSONObject("send").put("services", dst)
                    save(next, "通知服务已删除")
                    dialogState = null
                }
            },
        )
    }
}

@Composable
private fun ModelsConfig(
    config: JSONObject,
    save: (JSONObject, String) -> Unit,
    onMessage: (String) -> Unit,
) {
    var dialogState by remember { mutableStateOf<ModelDialogState?>(null) }
    val models = config.optJSONObject("llm")?.optJSONArray("models") ?: JSONArray()

    ConfigList("模型配置", "新增模型", { dialogState = ModelDialogState(null, null) }) {
        if (models.length() == 0) EmptyHint("还没有模型配置")
        for (i in 0 until models.length()) {
            val item = models.optJSONObject(i) ?: continue
            ConfigItem(
                title = item.optString("name", "未命名模型"),
                subtitle = buildModelSubtitle(item),
                detail = buildModelDetail(item),
                onClick = { dialogState = ModelDialogState(i, JSONObject(item.toString())) },
            )
        }
    }

    dialogState?.let { state ->
        ModelDialog(
            initialModel = state.model,
            onDismiss = { dialogState = null },
            onConfirm = { model ->
                val next = JSONObject(config.toString())
                val array = next.getJSONObject("llm").getJSONArray("models")
                if (hasDuplicateName(array, model.optString("name"), state.index)) {
                    onMessage("模型名称不能重复")
                    return@ModelDialog
                }
                if (state.index == null) {
                    array.put(model)
                    save(next, "模型已新增")
                } else {
                    array.put(state.index, model)
                    save(next, "模型已保存")
                }
                dialogState = null
            },
            onDelete = if (state.index == null) null else {
                {
                    val next = JSONObject(config.toString())
                    val src = next.getJSONObject("llm").getJSONArray("models")
                    val dst = JSONArray()
                    for (i in 0 until src.length()) if (i != state.index) dst.put(src.get(i))
                    next.getJSONObject("llm").put("models", dst)
                    save(next, "模型已删除")
                    dialogState = null
                }
            },
        )
    }
}

@Composable
private fun GlobalConfig(config: JSONObject, save: (JSONObject, String) -> Unit) {
    val ykt = config.optJSONObject("yuketang") ?: JSONObject()
    val send = config.optJSONObject("send") ?: JSONObject()
    val llm = config.optJSONObject("llm") ?: JSONObject()
    val util = config.optJSONObject("util") ?: JSONObject()
    var yktTimeout by remember(config.toString()) { mutableStateOf(ykt.optInt("timeout", 30).toString()) }
    var sendTimeout by remember(config.toString()) { mutableStateOf(send.optInt("timeout", 30).toString()) }
    var sendThreads by remember(config.toString()) { mutableStateOf(send.optInt("threads", 5).toString()) }
    var llmTimeout by remember(config.toString()) { mutableStateOf(llm.optInt("timeout", 60).toString()) }
    var llmThreads by remember(config.toString()) { mutableStateOf(llm.optInt("threads", 5).toString()) }
    var utilTimeout by remember(config.toString()) { mutableStateOf(util.optInt("timeout", 30).toString()) }
    var utilThreads by remember(config.toString()) { mutableStateOf(util.optInt("threads", 10).toString()) }
    var timezone by remember(config.toString()) { mutableStateOf(util.optString("timezone", "Asia/Shanghai")) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        CardBlock {
            Text("总配置", color = Ink, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(10.dp))
            FormField("雨课堂超时秒数", yktTimeout) { yktTimeout = it }
            FormField("通知超时秒数", sendTimeout) { sendTimeout = it }
            FormField("通知线程数", sendThreads) { sendThreads = it }
            FormField("模型超时秒数", llmTimeout) { llmTimeout = it }
            FormField("模型线程数", llmThreads) { llmThreads = it }
            FormField("工具超时秒数", utilTimeout) { utilTimeout = it }
            FormField("工具线程数", utilThreads) { utilThreads = it }
            FormField("时区", timezone) { timezone = it }
            Spacer(Modifier.height(12.dp))
            Button(
                onClick = {
                    val next = JSONObject(config.toString())
                    next.getJSONObject("yuketang").put("timeout", yktTimeout.toIntOrNull() ?: 30)
                    next.getJSONObject("send").put("timeout", sendTimeout.toIntOrNull() ?: 30)
                    next.getJSONObject("send").put("threads", sendThreads.toIntOrNull() ?: 5)
                    next.getJSONObject("llm").put("timeout", llmTimeout.toIntOrNull() ?: 60)
                    next.getJSONObject("llm").put("threads", llmThreads.toIntOrNull() ?: 5)
                    next.getJSONObject("util").put("timeout", utilTimeout.toIntOrNull() ?: 30)
                    next.getJSONObject("util").put("threads", utilThreads.toIntOrNull() ?: 10)
                    next.getJSONObject("util").put("timezone", timezone.ifBlank { "Asia/Shanghai" })
                    save(next, "总配置已保存")
                },
                modifier = Modifier.fillMaxWidth().height(46.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Primary),
            ) {
                Text("保存")
            }
        }
    }
}

@Composable
private fun JsonConfig(
    configFile: File,
    text: String,
    onTextChange: (String) -> Unit,
    onReload: () -> Unit,
    onMessage: (String) -> Unit,
) {
    val context = LocalContext.current
    var editing by remember { mutableStateOf(false) }
    Column(modifier = Modifier.fillMaxSize()) {
        Text("高级 JSON 编辑", color = Ink, fontWeight = FontWeight.Bold)
        Text("表单无法覆盖的字段可在这里兜底修改", color = Muted, fontSize = 13.sp)
        Spacer(Modifier.height(10.dp))
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .background(Color.White, RoundedCornerShape(10.dp))
                .verticalScroll(rememberScrollState())
                .horizontalScroll(rememberScrollState())
                .padding(12.dp),
        ) {
            if (editing) {
                BasicTextField(
                    value = text,
                    onValueChange = onTextChange,
                    textStyle = TextStyle(
                        color = Color(0xFF111827),
                        fontSize = 13.sp,
                        fontFamily = FontFamily.Monospace,
                        lineHeight = 18.sp,
                    ),
                    modifier = Modifier.fillMaxWidth(),
                )
            } else {
                Text(
                    text = text,
                    color = Color(0xFF111827),
                    fontSize = 13.sp,
                    fontFamily = FontFamily.Monospace,
                    lineHeight = 18.sp,
                )
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 8.dp)) {
            OutlinedButton(onClick = { editing = !editing }, modifier = Modifier.weight(1f)) {
                Text(if (editing) "完成" else "编辑")
            }
            Button(
                onClick = {
                    try {
                        val obj = JSONObject(text)
                        ensureConfigDefaults(obj)
                        configFile.writeText(obj.toString(2) + "\n", Charsets.UTF_8)
                        onTextChange(obj.toString(2))
                        editing = false
                        onMessage("JSON 已保存")
                    } catch (e: Exception) {
                        onMessage("JSON 格式错误：${e.message}")
                    }
                },
                modifier = Modifier.weight(1f),
            ) {
                Text("保存")
            }
            OutlinedButton(onClick = onReload, modifier = Modifier.weight(1f)) {
                Text("重载")
            }
            OutlinedButton(
                onClick = {
                    copyText(context, "config.json", text)
                    onMessage("JSON 已复制")
                },
                modifier = Modifier.weight(1f),
            ) {
                Text("复制")
            }
        }
    }
}

@Composable
private fun LogsScreen(homeDir: File) {
    val context = LocalContext.current
    val logFile = File(homeDir, "runner.log")
    var text by remember { mutableStateOf(readText(logFile, "暂无日志")) }
    var message by remember { mutableStateOf("") }

    LaunchedEffect(homeDir) {
        while (true) {
            text = trimLog(readText(logFile, "暂无日志"))
            delay(2000)
        }
    }

    Column(modifier = Modifier.fillMaxSize()) {
        Text("运行日志", color = Ink, fontSize = 20.sp, fontWeight = FontWeight.Bold)
        Text("自动刷新，可复制后排查问题", color = Muted, fontSize = 13.sp)
        Spacer(Modifier.height(10.dp))
        Text(
            text = text,
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .background(Color.White, RoundedCornerShape(10.dp))
                .verticalScroll(rememberScrollState())
                .horizontalScroll(rememberScrollState())
                .padding(12.dp),
            color = Color(0xFF111827),
            fontSize = 12.sp,
            fontFamily = FontFamily.Monospace,
            lineHeight = 17.sp,
        )
        if (message.isNotBlank()) Text(message, color = Primary, fontSize = 13.sp, modifier = Modifier.padding(top = 8.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 8.dp)) {
            OutlinedButton(
                onClick = {
                    text = trimLog(readText(logFile, "暂无日志"))
                    message = "已刷新"
                },
                modifier = Modifier.weight(1f),
            ) { Text("刷新") }
            Button(
                onClick = {
                    copyText(context, "runner.log", text)
                    message = "日志已复制"
                },
                modifier = Modifier.weight(1f),
                colors = ButtonDefaults.buttonColors(containerColor = Primary),
            ) { Text("复制") }
            OutlinedButton(
                onClick = {
                    logFile.writeText("", Charsets.UTF_8)
                    text = ""
                    message = "日志已清空"
                },
                modifier = Modifier.weight(1f),
            ) { Text("清空") }
        }
    }
}

@Composable
private fun FilesScreen(homeDir: File) {
    val context = LocalContext.current
    val rootDir = remember(homeDir) { runtimeDataDir(homeDir) }
    var refreshTick by remember { mutableStateOf(0) }
    var editorState by remember { mutableStateOf<FileEditorState?>(null) }
    var message by remember { mutableStateOf("") }
    var currentDir by remember(rootDir) { mutableStateOf(loadSavedFileBrowserDir(homeDir, rootDir)) }
    val entries = remember(refreshTick, currentDir) { managedFiles(currentDir) }

    LaunchedEffect(homeDir, refreshTick) {
        runtimeDataDir(homeDir).mkdirs()
    }
    LaunchedEffect(currentDir.absolutePath) {
        currentDir = resolveExistingManagedDir(rootDir, currentDir)
        saveFileBrowserDir(homeDir, rootDir, currentDir)
    }

    Column(modifier = Modifier.fillMaxSize()) {
        Text("文件", color = Ink, fontSize = 20.sp, fontWeight = FontWeight.Bold)
        Text("运行数据目录结构，可保存、分享，文本文件可直接编辑", color = Muted, fontSize = 13.sp)
        Spacer(Modifier.height(10.dp))
        CardBlock {
            Text(currentDir.relativeTo(rootDir).invariantSeparatorsPath.ifBlank { "." }, color = Ink, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(
                    onClick = {
                        currentDir = if (currentDir.parentFile != null && currentDir != rootDir) currentDir.parentFile else rootDir
                    },
                    enabled = currentDir != rootDir,
                    modifier = Modifier.weight(1f),
                ) { Text("上一级") }
                OutlinedButton(
                    onClick = {
                        currentDir = rootDir
                    },
                    enabled = currentDir != rootDir,
                    modifier = Modifier.weight(1f),
                ) { Text("根目录") }
            }
        }
        Spacer(Modifier.height(10.dp))
        Column(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            if (entries.isEmpty()) {
                CardBlock {
                    Text("暂无文件", color = Muted)
                }
            } else {
                entries.forEach { file ->
                    CardBlock {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable(enabled = file.isDirectory) {
                                    if (file.isDirectory) currentDir = file
                                },
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Text(
                                file.name,
                                color = Ink,
                                fontWeight = FontWeight.Bold,
                                fontSize = 15.sp,
                                modifier = Modifier.weight(1f),
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                            if (file.isFile) {
                                IconButton(
                                    onClick = {
                                        shareManagedFile(context, file, file.name)
                                        message = "已打开分享面板"
                                    },
                                ) {
                                    Icon(Icons.Outlined.Share, contentDescription = "分享", tint = Accent)
                                }
                                IconButton(
                                    onClick = {
                                        saveManagedFileToDownloads(context, file, file.name)
                                        message = "已保存到下载"
                                    },
                                ) {
                                    Icon(Icons.Outlined.Download, contentDescription = "保存", tint = Primary)
                                }
                                IconButton(
                                    onClick = {
                                        if (isEditableTextFile(file)) {
                                            editorState = FileEditorState(file, TextFieldValue(readText(file, "")))
                                            message = ""
                                        } else {
                                            message = "该文件暂不支持直接编辑"
                                        }
                                    },
                                ) {
                                    Icon(Icons.Outlined.Edit, contentDescription = "编辑", tint = Ink)
                                }
                            }
                            IconButton(
                                onClick = {
                                    deleteManagedEntry(file)
                                    refreshTick += 1
                                    currentDir = resolveExistingManagedDir(rootDir, currentDir)
                                    message = "已删除 ${file.name}"
                                },
                            ) {
                                Icon(Icons.Outlined.Delete, contentDescription = "删除", tint = Color(0xFFDC2626))
                            }
                        }
                    }
                }
            }
        }
        if (message.isNotBlank()) {
            Text(message, color = Primary, fontSize = 13.sp, modifier = Modifier.padding(top = 8.dp))
        }
        OutlinedButton(
            onClick = {
                refreshTick += 1
                message = "已刷新"
            },
            modifier = Modifier
                .padding(top = 8.dp)
                .fillMaxWidth(),
        ) { Text("刷新") }
    }

    val state = editorState
    if (state != null) {
        AlertDialog(
            onDismissRequest = { editorState = null },
            confirmButton = {
                Button(
                    onClick = {
                        state.file.writeText(state.text.text, Charsets.UTF_8)
                        editorState = null
                        refreshTick += 1
                        message = "已保存 ${state.file.name}"
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = Primary),
                ) { Text("保存") }
            },
            dismissButton = {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    TextButton(onClick = {
                        shareManagedFile(context, state.file, state.file.name)
                    }) { Text("分享") }
                    TextButton(onClick = { editorState = null }) { Text("关闭") }
                }
            },
            title = { Text("编辑文件") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(state.file.name, color = Muted, fontSize = 13.sp)
                    OutlinedTextField(
                        value = state.text,
                        onValueChange = { editorState = state.copy(text = it) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = 240.dp),
                        colors = OutlinedTextFieldDefaults.colors(),
                        textStyle = TextStyle(
                            color = Ink,
                            fontSize = 13.sp,
                            fontFamily = FontFamily.Monospace,
                            lineHeight = 18.sp,
                        ),
                    )
                }
            },
        )
    }
}

@Composable
private fun QrScreen(homeDir: File) {
    val qrFile = latestQrCodeFile(homeDir)
    var lastModified by remember { mutableStateOf(0L) }

    LaunchedEffect(homeDir) {
        while (true) {
            lastModified = qrFile.lastModified()
            delay(2000)
        }
    }

    Column(modifier = Modifier.fillMaxSize()) {
        Text("扫码登录", color = Ink, fontSize = 20.sp, fontWeight = FontWeight.Bold)
        Text("服务需要登录时会生成二维码", color = Muted, fontSize = 13.sp)
        Spacer(Modifier.height(12.dp))
        val bitmap = remember(lastModified) {
            if (qrFile.exists()) BitmapFactory.decodeFile(qrFile.absolutePath) else null
        }
        CardBlock(modifier = Modifier.weight(1f).fillMaxWidth()) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                if (bitmap == null) {
                    Text("暂未生成二维码", color = Muted)
                } else {
                    Image(
                        bitmap = bitmap.asImageBitmap(),
                        contentDescription = "登录二维码",
                        modifier = Modifier.size(280.dp),
                    )
                }
            }
        }
        Text("更新时间：${fileTime(qrFile)}", modifier = Modifier.padding(top = 10.dp), color = Muted, fontSize = 13.sp)
    }
}

@Composable
private fun ConfigList(title: String, action: String, onAction: () -> Unit, content: @Composable ColumnScope.() -> Unit) {
    Column(modifier = Modifier.fillMaxSize()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(modifier = Modifier.weight(1f)) {
                Text(title, color = Ink, fontSize = 20.sp, fontWeight = FontWeight.Bold)
                Text("用表单维护常用字段，复杂字段可到 JSON 修改", color = Muted, fontSize = 13.sp)
            }
            Button(onClick = onAction, colors = ButtonDefaults.buttonColors(containerColor = Primary)) {
                Text(action)
            }
        }
        Spacer(Modifier.height(12.dp))
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            content = content,
        )
    }
}

@Composable
private fun ConfigItem(title: String, subtitle: String, detail: String, onClick: (() -> Unit)? = null) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .let { if (onClick != null) it.clickable(onClick = onClick) else it },
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
        Text(title, color = Ink, fontSize = 16.sp, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis)
        Spacer(Modifier.height(4.dp))
        Text(subtitle, color = Muted, fontSize = 13.sp)
        Spacer(Modifier.height(4.dp))
        Text(detail, color = Color(0xFF334155), fontSize = 13.sp, maxLines = 2, overflow = TextOverflow.Ellipsis)
        }
    }
}

@Composable
private fun AccountConfigItem(
    title: String,
    subtitle: String,
    detail: String,
    qrFile: File,
    onClick: () -> Unit,
    onQrClick: () -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Row(modifier = Modifier.padding(14.dp), verticalAlignment = Alignment.Top) {
            Column(modifier = Modifier.weight(1f)) {
                Text(title, color = Ink, fontSize = 16.sp, fontWeight = FontWeight.Bold, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Spacer(Modifier.height(4.dp))
                Text(subtitle, color = Muted, fontSize = 13.sp)
                Spacer(Modifier.height(6.dp))
                Text(detail, color = Color(0xFF334155), fontSize = 13.sp, maxLines = 5, overflow = TextOverflow.Ellipsis)
            }
            Spacer(Modifier.width(12.dp))
            Box(
                modifier = Modifier
                    .size(72.dp)
                    .background(Color(0xFFF8FAFC), RoundedCornerShape(10.dp))
                    .clickable(enabled = qrFile.exists(), onClick = onQrClick),
                contentAlignment = Alignment.Center,
            ) {
                if (qrFile.exists()) {
                    BitmapFactory.decodeFile(qrFile.absolutePath)?.let {
                        Image(bitmap = it.asImageBitmap(), contentDescription = "登录二维码", modifier = Modifier.size(64.dp))
                    } ?: Text("二维码", color = Muted, fontSize = 12.sp)
                } else {
                    Text("无二维码", color = Muted, fontSize = 12.sp)
                }
            }
        }
    }
}

@Composable
private fun EmptyHint(text: String) {
    CardBlock {
        Text(text, color = Muted, fontSize = 14.sp)
    }
}

@Composable
private fun UserDialog(
    serviceNames: List<String>,
    initialUser: JSONObject?,
    onDismiss: () -> Unit,
    onConfirm: (JSONObject) -> Unit,
    onDelete: (() -> Unit)? = null,
) {
    val context = LocalContext.current
    val lesson = initialUser?.optJSONObject("lesson") ?: JSONObject()
    val exam = initialUser?.optJSONObject("exam") ?: JSONObject()
    val other = initialUser?.optJSONObject("other") ?: JSONObject()
    var name by remember(initialUser?.toString()) { mutableStateOf(initialUser?.optString("name", "") ?: "") }
    var domain by remember(initialUser?.toString()) { mutableStateOf(initialUser?.optString("domain", "www.yuketang.cn") ?: "www.yuketang.cn") }
    var enabled by remember(initialUser?.toString()) { mutableStateOf(initialUser?.optBoolean("enabled", true) ?: true) }
    val lessonWhiteItems = remember(initialUser?.toString()) { lesson.optJSONArray("classroomWhiteList").toMutableStringList() }
    val lessonBlackItems = remember(initialUser?.toString()) { lesson.optJSONArray("classroomBlackList").toMutableStringList() }
    val lessonStartTimeItems = remember(initialUser?.toString()) { lesson.optJSONObject("classroomStartTimeDict").toMutableScheduleList() }
    var lessonLlm by remember(initialUser?.toString()) { mutableStateOf(lesson.optBoolean("llm", true)) }
    var lessonAn by remember(initialUser?.toString()) { mutableStateOf(lesson.optBoolean("an", false)) }
    var lessonPpt by remember(initialUser?.toString()) { mutableStateOf(lesson.optBoolean("ppt", true)) }
    var lessonSi by remember(initialUser?.toString()) { mutableStateOf(lesson.optBoolean("si", true)) }
    val examWhiteItems = remember(initialUser?.toString()) { exam.optJSONArray("classroomWhiteList").toMutableStringList() }
    var examLlm by remember(initialUser?.toString()) { mutableStateOf(exam.optBoolean("llm", false)) }
    var examAn by remember(initialUser?.toString()) { mutableStateOf(exam.optBoolean("an", false)) }
    var examPaper by remember(initialUser?.toString()) { mutableStateOf(exam.optBoolean("paper", false)) }
    var isMaster by remember(initialUser?.toString()) { mutableStateOf(exam.optBoolean("isMaster", false)) }
    var isSlave by remember(initialUser?.toString()) { mutableStateOf(exam.optBoolean("isSlave", false)) }
    var xAccessToken by remember(initialUser?.toString()) { mutableStateOf(exam.optString("x_access_token", "")) }
    val otherCodeItems = remember(initialUser?.toString()) { other.optJSONArray("classroomCodeList").toMutableStringList() }
    var selectedServices by remember(initialUser?.toString()) {
        mutableStateOf(
            buildSet {
                initialUser?.optJSONArray("services")?.let { arr ->
                    for (i in 0 until arr.length()) add(arr.optString(i))
                }
            }
        )
    }

    FormDialog(
        title = if (initialUser == null) "新增账号" else "编辑账号",
        onDismiss = onDismiss,
        onConfirm = {
            onConfirm(
                JSONObject()
                    .put("name", name.ifBlank { "user" })
                    .put("enabled", enabled)
                    .put("domain", domain.ifBlank { "www.yuketang.cn" })
                    .put("lesson", JSONObject()
                        .put("classroomWhiteList", lessonWhiteItems.toJsonArray())
                        .put("classroomBlackList", lessonBlackItems.toJsonArray())
                        .put("classroomStartTimeDict", lessonStartTimeItems.toJsonObject())
                        .put("llm", lessonLlm)
                        .put("an", lessonAn)
                        .put("ppt", lessonPpt)
                        .put("si", lessonSi))
                    .put("exam", JSONObject()
                        .put("classroomWhiteList", examWhiteItems.toJsonArray())
                        .put("llm", examLlm)
                        .put("an", examAn)
                        .put("paper", examPaper)
                        .put("isMaster", isMaster)
                        .put("isSlave", isSlave)
                        .put("x_access_token", xAccessToken))
                    .put("other", JSONObject().put("classroomCodeList", otherCodeItems.toJsonArray()))
                    .put("services", JSONArray().apply { selectedServices.forEach { put(it) } })
            )
        },
        extraButton = onDelete,
    ) {
        FormField("账号名称", name) { name = it }
        FormField("域名", domain) { domain = it }
        SwitchRow("启用账号", enabled) { enabled = it }
        HorizontalDivider()
        Text("课程配置", fontWeight = FontWeight.Bold, color = Ink)
        ListEditor("课程白名单", lessonWhiteItems)
        ListEditor("课程黑名单", lessonBlackItems)
        ScheduleEditor("上课时间", lessonStartTimeItems)
        SwitchRow("课程启用 LLM", lessonLlm) { lessonLlm = it }
        SwitchRow("课程自动答题", lessonAn) { lessonAn = it }
        SwitchRow("下载 PPT", lessonPpt) { lessonPpt = it }
        SwitchRow("推送当前页", lessonSi) { lessonSi = it }
        HorizontalDivider()
        Text("考试配置", fontWeight = FontWeight.Bold, color = Ink)
        ListEditor("考试白名单", examWhiteItems)
        FormField("x_access_token", xAccessToken) { xAccessToken = it }
        SwitchRow("考试启用 LLM", examLlm) { examLlm = it }
        SwitchRow("考试自动答题", examAn) { examAn = it }
        SwitchRow("保存试卷", examPaper) { examPaper = it }
        SwitchRow("主控模式", isMaster) { isMaster = it }
        SwitchRow("从属模式", isSlave) { isSlave = it }
        HorizontalDivider()
        Text("其它配置", fontWeight = FontWeight.Bold, color = Ink)
        ListEditor("课堂邀请码", otherCodeItems)
        HorizontalDivider()
        Text("通知服务", fontWeight = FontWeight.Bold, color = Ink)
        if (serviceNames.isEmpty()) {
            Text("请先在“通知”里新增服务", color = Muted, fontSize = 13.sp)
        } else {
            serviceNames.forEach { service ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Checkbox(
                        checked = selectedServices.contains(service),
                        onCheckedChange = { checked ->
                            selectedServices = if (checked) selectedServices + service else selectedServices - service
                        },
                    )
                    Spacer(Modifier.width(6.dp))
                    Text(service, color = Ink)
                }
            }
        }
    }
}

@Composable
private fun QrPreviewDialog(file: File, title: String, onDismiss: () -> Unit) {
    val context = LocalContext.current
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title, fontWeight = FontWeight.Bold) },
        text = {
            Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                BitmapFactory.decodeFile(file.absolutePath)?.let {
                    Image(bitmap = it.asImageBitmap(), contentDescription = "登录二维码", modifier = Modifier.size(280.dp))
                } ?: Text("二维码不可用", color = Muted)
            }
        },
        confirmButton = {
            Row {
                TextButton(onClick = { shareQr(context, file, title) }) { Text("分享") }
                TextButton(onClick = {
                    saveQrToDownloads(context, file, title)
                    Toast.makeText(context, "已保存到下载目录", Toast.LENGTH_SHORT).show()
                }) { Text("保存") }
                TextButton(onClick = onDismiss) { Text("关闭") }
            }
        },
    )
}

@Composable
private fun ServiceDialog(
    initialService: JSONObject?,
    onDismiss: () -> Unit,
    onConfirm: (JSONObject) -> Unit,
    onDelete: (() -> Unit)? = null,
) {
    val initialServiceType = initialService?.optString("type", "dingtalk") ?: "dingtalk"
    var type by remember(initialService?.toString()) { mutableStateOf(initialServiceType) }
    var name by remember(initialService?.toString()) { mutableStateOf(initialService?.optString("name", initialServiceType) ?: initialServiceType) }
    var enabled by remember(initialService?.toString()) { mutableStateOf(initialService?.optBoolean("enabled", true) ?: true) }
    var touser by remember(initialService?.toString()) { mutableStateOf(initialService?.optString("touser", "@all") ?: "@all") }
    var agentId by remember(initialService?.toString()) { mutableStateOf(initialService?.optString("agentId", "") ?: "") }
    var secret by remember(initialService?.toString()) { mutableStateOf(initialService?.optString("secret", "") ?: "") }
    var companyId by remember(initialService?.toString()) { mutableStateOf(initialService?.optString("companyId", "") ?: "") }
    var appKey by remember(initialService?.toString()) { mutableStateOf(initialService?.optString("appKey", "") ?: "") }
    var appSecret by remember(initialService?.toString()) { mutableStateOf(initialService?.optString("appSecret", "") ?: "") }
    var robotCode by remember(initialService?.toString()) { mutableStateOf(initialService?.optString("robotCode", "") ?: "") }
    var openConversationId by remember(initialService?.toString()) { mutableStateOf(initialService?.optString("openConversationId", "") ?: "") }
    var appId by remember(initialService?.toString()) { mutableStateOf(initialService?.optString("appId", "") ?: "") }
    var openId by remember(initialService?.toString()) { mutableStateOf(initialService?.optString("openId", "") ?: "") }
    var msgLimit by remember(initialService?.toString()) { mutableStateOf((initialService?.optInt("msgLimit") ?: defaultServiceTemplate(initialServiceType).optInt("msgLimit")).toString()) }
    var dataLimit by remember(initialService?.toString()) { mutableStateOf((initialService?.optLong("dataLimit") ?: defaultServiceTemplate(initialServiceType).optLong("dataLimit")).toString()) }

    fun applyTemplate(newType: String) {
        val t = defaultServiceTemplate(newType)
        if (name.isBlank() || name == type) name = t.optString("name", newType)
        type = newType
        msgLimit = t.optInt("msgLimit").toString()
        dataLimit = t.optLong("dataLimit").toString()
    }

    FormDialog(
        title = if (initialService == null) "新增通知服务" else "编辑通知服务",
        onDismiss = onDismiss,
        onConfirm = {
            val obj = JSONObject()
                .put("name", name.ifBlank { type })
                .put("enabled", enabled)
                .put("type", type)
                .put("msgLimit", msgLimit.toIntOrNull() ?: defaultServiceTemplate(type).optInt("msgLimit"))
                .put("dataLimit", dataLimit.toLongOrNull() ?: defaultServiceTemplate(type).optLong("dataLimit"))
            when (type) {
                "wechat" -> obj.put("touser", touser).put("agentId", agentId).put("secret", secret).put("companyId", companyId)
                "feishu" -> obj.put("appId", appId).put("appSecret", appSecret).put("openId", openId)
                else -> obj.put("appKey", appKey).put("appSecret", appSecret).put("robotCode", robotCode).put("openConversationId", openConversationId)
            }
            onConfirm(obj)
        },
        extraButton = onDelete,
    ) {
        TypeSelector("服务类型", type, SERVICE_TYPES, ::applyTemplate, itemLabel = ::serviceTypeLabel)
        FormField("服务名称", name) { name = it }
        SwitchRow("启用服务", enabled) { enabled = it }
        when (type) {
            "wechat" -> {
                FormField("touser", touser) { touser = it }
                FormField("agentId", agentId) { agentId = it }
                FormField("secret", secret) { secret = it }
                FormField("companyId", companyId) { companyId = it }
            }
            "feishu" -> {
                FormField("appId", appId) { appId = it }
                FormField("appSecret", appSecret) { appSecret = it }
                FormField("openId", openId) { openId = it }
            }
            else -> {
                FormField("appKey", appKey) { appKey = it }
                FormField("appSecret", appSecret) { appSecret = it }
                FormField("robotCode", robotCode) { robotCode = it }
                FormField("openConversationId", openConversationId) { openConversationId = it }
            }
        }
        FormField("msgLimit", msgLimit) { msgLimit = it }
        FormField("dataLimit", dataLimit) { dataLimit = it }
    }
}

@Composable
private fun ModelDialog(
    initialModel: JSONObject?,
    onDismiss: () -> Unit,
    onConfirm: (JSONObject) -> Unit,
    onDelete: (() -> Unit)? = null,
) {
    val initialModelType = initialModel?.optString("type", "openai") ?: "openai"
    var type by remember(initialModel?.toString()) { mutableStateOf(initialModelType) }
    var name by remember(initialModel?.toString()) { mutableStateOf(initialModel?.optString("name", defaultModelTemplate(initialModelType).optString("name")) ?: defaultModelTemplate(initialModelType).optString("name")) }
    var enabled by remember(initialModel?.toString()) { mutableStateOf(initialModel?.optBoolean("enabled", true) ?: true) }
    var apiKey by remember(initialModel?.toString()) { mutableStateOf(initialModel?.optString("apiKey", "") ?: "") }
    var model by remember(initialModel?.toString()) { mutableStateOf(initialModel?.optString("model", defaultModelTemplate(initialModelType).optString("model")) ?: defaultModelTemplate(initialModelType).optString("model")) }
    var prompt by remember(initialModel?.toString()) { mutableStateOf(initialModel?.optString("prompt", "You are a helpful assistant.") ?: "You are a helpful assistant.") }
    var temperature by remember(initialModel?.toString()) { mutableStateOf((initialModel?.optDouble("temperature") ?: defaultModelTemplate(initialModelType).optDouble("temperature", 1.0)).toString()) }
    var score by remember(initialModel?.toString()) { mutableStateOf((initialModel?.optInt("score") ?: defaultModelTemplate(initialModelType).optInt("score", 100)).toString()) }
    var accountId by remember(initialModel?.toString()) { mutableStateOf(initialModel?.optString("accountId", "") ?: "") }
    var apiToken by remember(initialModel?.toString()) { mutableStateOf(initialModel?.optString("apiToken", "") ?: "") }
    var accessToken by remember(initialModel?.toString()) { mutableStateOf(initialModel?.optString("accessToken", "") ?: "") }
    var accessKeyId by remember(initialModel?.toString()) { mutableStateOf(initialModel?.optString("accessKeyId", "") ?: "") }
    var accessKeySecret by remember(initialModel?.toString()) { mutableStateOf(initialModel?.optString("accessKeySecret", "") ?: "") }

    fun applyTemplate(newType: String) {
        val t = defaultModelTemplate(newType)
        if (name.isBlank() || name == defaultModelTemplate(type).optString("name")) name = t.optString("name")
        model = t.optString("model")
        temperature = t.optDouble("temperature", 1.0).toString()
        score = t.optInt("score", 100).toString()
        prompt = t.optString("prompt", "You are a helpful assistant.")
        type = newType
    }

    FormDialog(
        title = if (initialModel == null) "新增模型" else "编辑模型",
        onDismiss = onDismiss,
        onConfirm = {
            val obj = JSONObject()
                .put("name", name.ifBlank { model.ifBlank { "model" } })
                .put("enabled", enabled)
                .put("type", type)
                .put("model", model)
                .put("prompt", prompt)
                .put("temperature", temperature.toDoubleOrNull() ?: defaultModelTemplate(type).optDouble("temperature", 1.0))
                .put("score", score.toIntOrNull() ?: 100)
            when (type) {
                "cloudflare" -> obj.put("accountId", accountId).put("apiToken", apiToken)
                "modelscope" -> obj.put("accessToken", accessToken)
                "sensecore" -> obj.put("accessKeyId", accessKeyId).put("accessKeySecret", accessKeySecret)
                else -> obj.put("apiKey", apiKey)
            }
            onConfirm(obj)
        },
        extraButton = onDelete,
    ) {
        TypeSelector("模型类型", type, MODEL_TYPES, ::applyTemplate)
        FormField("配置名称", name) { name = it }
        SwitchRow("启用模型", enabled) { enabled = it }
        when (type) {
            "cloudflare" -> {
                FormField("accountId", accountId) { accountId = it }
                FormField("apiToken", apiToken) { apiToken = it }
            }
            "modelscope" -> {
                FormField("accessToken", accessToken) { accessToken = it }
            }
            "sensecore" -> {
                FormField("accessKeyId", accessKeyId) { accessKeyId = it }
                FormField("accessKeySecret", accessKeySecret) { accessKeySecret = it }
            }
            else -> {
                FormField("apiKey", apiKey) { apiKey = it }
            }
        }
        FormField("模型名", model) { model = it }
        FormField("Prompt", prompt) { prompt = it }
        FormField("Temperature", temperature) { temperature = it }
        FormField("Score", score) { score = it }
    }
}

@Composable
private fun FormDialog(
    title: String,
    onDismiss: () -> Unit,
    onConfirm: () -> Unit,
    extraButton: (() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title, fontWeight = FontWeight.Bold) },
        text = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(10.dp),
                content = content,
            )
        },
        confirmButton = {
            Button(onClick = onConfirm, colors = ButtonDefaults.buttonColors(containerColor = Primary)) {
                Text("保存")
            }
        },
        dismissButton = {
            Row(verticalAlignment = Alignment.CenterVertically) {
                if (extraButton != null) {
                    TextButton(onClick = extraButton) {
                        Text("删除", color = Color(0xFFDC2626))
                    }
                }
                TextButton(onClick = onDismiss) {
                    Text("取消")
                }
            }
        },
    )
}

@Composable
private fun FormField(label: String, value: String, onChange: (String) -> Unit) {
    OutlinedTextField(
        value = value,
        onValueChange = onChange,
        label = { Text(label) },
        modifier = Modifier.fillMaxWidth(),
        singleLine = false,
    )
}

@Composable
private fun SwitchRow(label: String, checked: Boolean, onChange: (Boolean) -> Unit) {
    Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Text(label, modifier = Modifier.weight(1f), color = Ink)
        Switch(checked = checked, onCheckedChange = onChange)
    }
}

@Composable
private fun CardBlock(modifier: Modifier = Modifier, content: @Composable ColumnScope.() -> Unit) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(modifier = Modifier.padding(14.dp), content = content)
    }
}

@Composable
private fun MetricCard(label: String, value: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .background(Color(0xFFF1F5F9), RoundedCornerShape(10.dp))
            .padding(12.dp),
    ) {
        Text(label, color = Muted, fontSize = 12.sp)
        Text(value, color = Ink, fontSize = 17.sp, fontWeight = FontWeight.Bold, maxLines = 1)
    }
}

@Composable
private fun InfoRow(label: String, value: String) {
    Row(modifier = Modifier.fillMaxWidth().padding(vertical = 5.dp)) {
        Text(label, color = Muted, fontSize = 13.sp, modifier = Modifier.weight(0.32f))
        Text(value, color = Ink, fontSize = 13.sp, modifier = Modifier.weight(0.68f))
    }
    HorizontalDivider(color = Color(0xFFE2E8F0))
}

@Composable
private fun StatusPill(text: String, color: Color) {
    Text(
        text = text,
        color = color,
        fontSize = 13.sp,
        fontWeight = FontWeight.Bold,
        modifier = Modifier.background(color.copy(alpha = 0.12f), RoundedCornerShape(999.dp)).padding(horizontal = 12.dp, vertical = 6.dp),
    )
}

private fun stateLabel(state: String): String = when (state) {
    "running" -> "运行中"
    "starting" -> "启动中"
    "stopping" -> "停止中"
    "error" -> "异常"
    else -> "已停止"
}

private fun statusColor(state: String): Color = when (state) {
    "running" -> Primary
    "starting", "stopping" -> Accent
    "error" -> Color(0xFFDC2626)
    else -> Muted
}

private fun readJson(file: File): JSONObject = runCatching { JSONObject(readText(file, "{}")) }.getOrElse { JSONObject() }

private fun countEnabledUsers(configFile: File): Int = runCatching {
    val users = JSONObject(readText(configFile, DEFAULT_CONFIG)).getJSONObject("yuketang").getJSONArray("users")
    var count = 0
    for (i in 0 until users.length()) if (users.getJSONObject(i).optBoolean("enabled")) count += 1
    count
}.getOrDefault(0)

private fun ensureConfigDefaults(config: JSONObject) {
    val ykt = config.optJSONObject("yuketang") ?: JSONObject().also { config.put("yuketang", it) }
    if (!ykt.has("users")) ykt.put("users", JSONArray())
    if (!ykt.has("timeout")) ykt.put("timeout", 30)
    val send = config.optJSONObject("send") ?: JSONObject().also { config.put("send", it) }
    if (!send.has("services")) send.put("services", JSONArray())
    if (!send.has("threads")) send.put("threads", 5)
    if (!send.has("timeout")) send.put("timeout", 30)
    val llm = config.optJSONObject("llm") ?: JSONObject().also { config.put("llm", it) }
    if (!llm.has("models")) llm.put("models", JSONArray())
    if (!llm.has("threads")) llm.put("threads", 5)
    if (!llm.has("timeout")) llm.put("timeout", 60)
    val util = config.optJSONObject("util") ?: JSONObject().also { config.put("util", it) }
    if (!util.has("threads")) util.put("threads", 10)
    if (!util.has("timeout")) util.put("timeout", 30)
    if (!util.has("timezone")) util.put("timezone", "Asia/Shanghai")
}

private fun normalizeName(name: String): String {
    return name.trim().lowercase(Locale.ROOT)
}

private fun hasDuplicateName(array: JSONArray, name: String, currentIndex: Int?): Boolean {
    val normalized = normalizeName(name)
    if (normalized.isBlank()) return false
    for (i in 0 until array.length()) {
        if (currentIndex != null && i == currentIndex) continue
        val current = array.optJSONObject(i)?.optString("name").orEmpty()
        if (normalizeName(current) == normalized) return true
    }
    return false
}

private fun JSONArray.joinText(): String {
    val values = mutableListOf<String>()
    for (i in 0 until length()) values.add(optString(i))
    return values.joinToString("、")
}

private fun JSONArray.joinComma(): String {
    val values = mutableListOf<String>()
    for (i in 0 until length()) values.add(optString(i))
    return values.joinToString(",")
}

private fun buildUserSubtitle(user: JSONObject): String {
    val domain = user.optString("domain", "-")
    val enabled = if (user.optBoolean("enabled")) "已启用" else "已停用"
    return "$domain · $enabled"
}

private fun buildUserDetail(user: JSONObject): String {
    val lesson = user.optJSONObject("lesson") ?: JSONObject()
    val exam = user.optJSONObject("exam") ?: JSONObject()
    val other = user.optJSONObject("other") ?: JSONObject()
    val services = user.optJSONArray("services")?.joinText().orEmpty().ifBlank { "-" }
    val lessonWhite = lesson.optJSONArray("classroomWhiteList")?.joinText().orEmpty().ifBlank { "-" }
    val lessonBlack = lesson.optJSONArray("classroomBlackList")?.joinText().orEmpty().ifBlank { "-" }
    val examWhite = exam.optJSONArray("classroomWhiteList")?.joinText().orEmpty().ifBlank { "-" }
    val lessonTime = lesson.optJSONObject("classroomStartTimeDict")?.toString()?.ifBlank { "-" } ?: "-"
    val codes = other.optJSONArray("classroomCodeList")?.joinText().orEmpty().ifBlank { "-" }
    return "课程白名单：$lessonWhite\n课程黑名单：$lessonBlack\n上课时间：$lessonTime\n考试白名单：$examWhite\n其他邀请码：$codes\n通知服务：$services"
}

private fun buildServiceSubtitle(service: JSONObject): String {
    return "${service.optString("type", "-")} · ${if (service.optBoolean("enabled")) "已启用" else "已停用"}"
}

private fun buildServiceDetail(service: JSONObject): String {
    val key = when (service.optString("type")) {
        "wechat" -> service.optString("touser", "-")
        "feishu" -> service.optString("openId", "-")
        else -> service.optString("openConversationId", "-")
    }
    return "目标：$key\n消息上限：${service.optInt("msgLimit", 0)} · 数据上限：${service.optLong("dataLimit", 0)}"
}

private fun buildModelSubtitle(model: JSONObject): String {
    return "${model.optString("type", "-")} · ${model.optString("model", "-")}"
}

private fun buildModelDetail(model: JSONObject): String {
    val auth = when (model.optString("type")) {
        "cloudflare" -> "accountId"
        "modelscope" -> "accessToken"
        "sensecore" -> "accessKeyId"
        else -> "apiKey"
    }
    return "鉴权：$auth · 分值：${model.optInt("score", 100)} · ${if (model.optBoolean("enabled")) "已启用" else "已停用"}"
}

@Composable
private fun TypeSelector(
    label: String,
    selected: String,
    items: List<String>,
    onSelected: (String) -> Unit,
    itemLabel: (String) -> String = { it },
) {
    Column {
        if (label.isNotBlank()) {
            Text(label, color = Ink, fontWeight = FontWeight.Bold, fontSize = 14.sp)
            Spacer(Modifier.height(6.dp))
        }
        Row(
            modifier = Modifier.horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            items.forEach { item ->
                if (item == selected) {
                    Button(onClick = { onSelected(item) }, colors = ButtonDefaults.buttonColors(containerColor = Accent)) {
                        Text(itemLabel(item))
                    }
                } else {
                    OutlinedButton(onClick = { onSelected(item) }) {
                        Text(itemLabel(item))
                    }
                }
            }
        }
    }
}

private data class UserDialogState(
    val index: Int?,
    val user: JSONObject?,
)

private data class ServiceDialogState(
    val index: Int?,
    val service: JSONObject?,
)

private data class ModelDialogState(
    val index: Int?,
    val model: JSONObject?,
)

private fun defaultServiceTemplate(type: String): JSONObject = when (type) {
    "wechat" -> JSONObject()
        .put("name", "wechat")
        .put("enabled", true)
        .put("type", "wechat")
        .put("touser", "@all")
        .put("agentId", "")
        .put("secret", "")
        .put("companyId", "")
        .put("msgLimit", 500)
        .put("dataLimit", 20971520)
    "feishu" -> JSONObject()
        .put("name", "feishu")
        .put("enabled", true)
        .put("type", "feishu")
        .put("appId", "")
        .put("appSecret", "")
        .put("openId", "")
        .put("msgLimit", 10000)
        .put("dataLimit", 31457280)
    else -> JSONObject()
        .put("name", "dingtalk")
        .put("enabled", true)
        .put("type", "dingtalk")
        .put("appKey", "")
        .put("appSecret", "")
        .put("robotCode", "")
        .put("openConversationId", "")
        .put("msgLimit", 3000)
        .put("dataLimit", 20971520)
}

private fun defaultModelTemplate(type: String): JSONObject = when (type) {
    "claude" -> commonModelTemplate("claude-opus-4-6", "claude", "claude-opus-4-6", 0.2)
    "grok" -> commonModelTemplate("grok-4.20-0309-reasoning", "grok", "grok-4.20-0309-reasoning", 0.2)
    "gemini" -> commonModelTemplate("gemini-3-flash-preview", "gemini", "gemini-3-flash-preview", 0.2)
    "cloudflare" -> commonModelTemplate("cloudflare-kimi-k2.5", "cloudflare", "@cf/moonshotai/kimi-k2.5", 0.2)
        .put("accountId", "").put("apiToken", "")
    "openrouter" -> commonModelTemplate("openrouter-gpt-oss-120b", "openrouter", "openai/gpt-oss-120b:free", 0.2)
    "poixe" -> commonModelTemplate("poixe-gpt-5.2", "poixe", "gpt-5.2:free", 0.2)
    "siliconflow" -> commonModelTemplate("siliconflow-Kimi-K2.5", "siliconflow", "Pro/moonshotai/Kimi-K2.5", 0.2)
    "infinigence" -> commonModelTemplate("infinigence-kimi-k2.5", "infinigence", "kimi-k2.5", 0.2)
    "zhipu" -> commonModelTemplate("zhipu-glm-5v-turbo", "zhipu", "glm-5v-turbo", 0.2)
    "dmxapi" -> commonModelTemplate("dmxapi-glm-4.1v-9b-thinking", "dmxapi", "GLM-4.1V-9B-Thinking", 0.2)
    "modelscope" -> commonModelTemplate("modelscope-Kimi-K2.5", "modelscope", "moonshotai/Kimi-K2.5", 0.2)
        .put("accessToken", "")
    "moonshot" -> commonModelTemplate("moonshot-kimi-k2.5", "moonshot", "kimi-k2.5", 1.0)
    "volcengine" -> commonModelTemplate("volcengine-doubao-seed-2-0-pro-260215", "volcengine", "doubao-seed-2-0-pro-260215", 0.2)
    "poloapi" -> commonModelTemplate("poloapi-gemini-2.5-flash", "poloapi", "gemini-2.5-flash", 0.2)
    "bailian" -> commonModelTemplate("bailian-qwen3.6-plus", "bailian", "qwen3.6-plus", 0.2)
    "qianfan" -> commonModelTemplate("qianfan-ernie-5.0-thinking-preview", "qianfan", "ernie-5.0-thinking-preview", 0.2)
    "xunfei" -> commonModelTemplate("xunfei-xop3qwen32bvl", "xunfei", "xop3qwen32bvl", 0.2)
    "minimax" -> commonModelTemplate("minimax-MiniMax-M2.7", "minimax", "MiniMax-M2.7", 0.2)
    "sensecore" -> commonModelTemplate("sensecore-SenseNova-V6-Pro", "sensecore", "SenseNova-V6-Pro", 0.2)
        .put("accessKeyId", "").put("accessKeySecret", "")
    "mistral" -> commonModelTemplate("mistral-mistral-small-latest", "mistral", "mistral-small-latest", 0.2)
    "tencent" -> commonModelTemplate("tencent-kimi-k2.5", "tencent", "kimi-k2.5", 0.2)
    "cohere" -> commonModelTemplate("cohere-command-a-vision-07-2025", "cohere", "command-a-vision-07-2025", 0.2)
    else -> commonModelTemplate("openai-gpt-5.4", "openai", "gpt-5.4", 1.0)
}

private fun commonModelTemplate(name: String, type: String, model: String, temperature: Double): JSONObject =
    JSONObject()
        .put("name", name)
        .put("enabled", true)
        .put("type", type)
        .put("apiKey", "")
        .put("model", model)
        .put("prompt", "You are a helpful assistant.")
        .put("temperature", temperature)
        .put("score", 100)

private val SERVICE_TYPES = listOf("wechat", "dingtalk", "feishu")
private val MODEL_TYPES = listOf(
    "openai", "claude", "grok", "gemini", "cloudflare", "openrouter", "poixe",
    "siliconflow", "infinigence", "zhipu", "dmxapi", "modelscope", "moonshot",
    "volcengine", "poloapi", "bailian", "qianfan", "xunfei", "minimax",
    "sensecore", "mistral", "tencent", "cohere"
)

private fun serviceTypeLabel(type: String): String = when (type) {
    "wechat" -> "企业微信"
    "dingtalk" -> "钉钉"
    "feishu" -> "飞书"
    else -> type
}

private fun String.toJsonArray(): JSONArray {
    val arr = JSONArray()
    split(",", "，", "\n").map { it.trim() }.filter { it.isNotBlank() }.forEach { arr.put(it) }
    return arr
}

private fun String.toJsonObject(): JSONObject {
    return runCatching {
        val text = trim()
        if (text.isBlank()) JSONObject() else JSONObject(text)
    }.getOrElse { JSONObject() }
}

private fun sanitizeForFileName(name: String): String {
    return name
        .replace(Regex("[\\u0000-\\u001f]"), "")
        .replace(Regex("[\\\\/:*?\"<>|]"), "_")
        .ifBlank { "user" }
}

private fun qrDir(homeDir: File): File = File(runtimeDataDir(homeDir), "qr")

private fun cookieDir(homeDir: File): File = File(runtimeDataDir(homeDir), "cookie")

private fun tokenDir(homeDir: File): File = File(runtimeDataDir(homeDir), "token")

private fun fileDir(homeDir: File): File = File(runtimeDataDir(homeDir), "file")

private fun qrCodeFileForName(homeDir: File, name: String): File {
    return File(qrDir(homeDir), "qrcode_${sanitizeForFileName(name)}.jpg")
}

private fun latestQrCodeFile(homeDir: File): File {
    return homeDir.listFiles()
        ?.filter { it.isFile && it.name.startsWith("qrcode_") && it.name.endsWith(".jpg") }
        ?.maxByOrNull { it.lastModified() }
        ?: File(homeDir, "qrcode.jpg")
}

private fun trimLog(text: String): String = if (text.length > 20000) text.takeLast(20000) else text

private fun readText(file: File, fallback: String): String = runCatching {
    if (file.exists()) file.readText(Charsets.UTF_8) else fallback
}.getOrDefault(fallback)

private fun fileTime(file: File): String {
    if (!file.exists()) return "-"
    return SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US).format(Date(file.lastModified()))
}

private fun mimeTypeFor(file: File): String {
    return when (file.extension.lowercase(Locale.ROOT)) {
        "jpg", "jpeg" -> "image/jpeg"
        "png" -> "image/png"
        "pdf" -> "application/pdf"
        "json" -> "application/json"
        "txt", "log", "md", "py", "csv" -> "text/plain"
        else -> "application/octet-stream"
    }
}

private fun isEditableTextFile(file: File): Boolean {
    return file.extension.lowercase(Locale.ROOT) in setOf("json", "txt", "log", "md", "py", "csv")
}

private fun Long.readableFileSize(): String {
    val size = this.toDouble()
    if (size < 1024) return "${this} B"
    if (size < 1024 * 1024) return String.format(Locale.US, "%.1f KB", size / 1024)
    return String.format(Locale.US, "%.1f MB", size / (1024 * 1024))
}

private fun copyText(context: Context, label: String, text: String) {
    val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
    clipboard.setPrimaryClip(ClipData.newPlainText(label, text))
    Toast.makeText(context, "已复制", Toast.LENGTH_SHORT).show()
}

@Composable
private fun ListEditor(label: String, items: MutableList<String>) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(label, color = Ink, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
            TextButton(onClick = { items.add("") }) { Text("+") }
        }
        if (items.isNotEmpty()) {
            items.forEachIndexed { index, value ->
                Row(verticalAlignment = Alignment.CenterVertically) {
                    OutlinedTextField(
                        value = value,
                        onValueChange = { items[index] = it },
                        label = { Text("${label} ${index + 1}") },
                        modifier = Modifier.weight(1f),
                    )
                    TextButton(onClick = { items.removeAt(index) }, modifier = Modifier.widthIn(min = 52.dp)) {
                        Text("-")
                    }
                }
            }
        }
    }
}

@Composable
private fun ScheduleEditor(label: String, items: MutableList<ScheduleEntry>) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(label, color = Ink, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
            TextButton(onClick = { items.add(ScheduleEntry("", mutableStateListOf())) }) { Text("+") }
        }
        if (items.isNotEmpty()) {
            items.forEachIndexed { index, entry ->
                CardBlock {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("课程 ${index + 1}", color = Ink, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                        TextButton(onClick = { items.removeAt(index) }) { Text("-") }
                    }
                    OutlinedTextField(
                        value = entry.name,
                        onValueChange = { items[index] = entry.copy(name = it) },
                        label = { Text("课程名称") },
                        modifier = Modifier.fillMaxWidth(),
                    )
                    WeekTimeEditor(entry.times)
                }
            }
        }
    }
}

@Composable
private fun WeekTimeEditor(items: SnapshotStateList<WeekTimeEntry>) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("各日时间", color = Ink, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
            TextButton(onClick = { items.add(WeekTimeEntry("1", "08:00")) }) { Text("+") }
        }
        items.forEachIndexed { index, entry ->
            WeekTimeRow(
                entry = entry,
                onChange = { items[index] = it },
                onDelete = { items.removeAt(index) },
            )
        }
    }
}

@Composable
private fun WeekTimeRow(entry: WeekTimeEntry, onChange: (WeekTimeEntry) -> Unit, onDelete: () -> Unit) {
    val context = LocalContext.current
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color(0xFFF8FAFC), RoundedCornerShape(10.dp))
            .padding(10.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(WEEK_DAYS[entry.weekDay] ?: entry.weekDay, color = Ink, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
            TextButton(onClick = onDelete) { Text("-") }
        }
        TypeSelector(
            label = "",
            selected = entry.weekDay,
            items = WEEK_DAYS.keys.toList(),
            onSelected = { onChange(entry.copy(weekDay = it)) },
            itemLabel = { WEEK_DAYS[it] ?: it },
        )
        OutlinedButton(
            onClick = {
                val parts = entry.time.split(":")
                val hour = parts.getOrNull(0)?.toIntOrNull() ?: 8
                val minute = parts.getOrNull(1)?.toIntOrNull() ?: 0
                TimePickerDialog(context, { _, h, m ->
                    onChange(entry.copy(time = "%02d:%02d".format(h, m)))
                }, hour, minute, true).show()
            },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("时间：${entry.time.ifBlank { "选择时间" }}")
        }
    }
}

private fun JSONArray?.toMutableStringList() = mutableStateListOf<String>().apply {
    if (this@toMutableStringList != null) {
        for (i in 0 until this@toMutableStringList.length()) add(this@toMutableStringList.optString(i))
    }
}

private fun JSONObject?.toMutableScheduleList() = mutableStateListOf<ScheduleEntry>().apply {
    if (this@toMutableScheduleList != null) {
        val keys = this@toMutableScheduleList.keys()
        while (keys.hasNext()) {
            val key = keys.next()
            add(ScheduleEntry(key, this@toMutableScheduleList.optJSONObject(key).toMutableWeekTimeList()))
        }
    }
}

private fun MutableList<String>.toJsonArray(): JSONArray = JSONArray().apply {
    this@toJsonArray.map { it.trim() }.filter { it.isNotBlank() }.forEach { put(it) }
}

private fun MutableList<ScheduleEntry>.toJsonObject(): JSONObject = JSONObject().apply {
    this@toJsonObject.filter { it.name.trim().isNotBlank() }
        .forEach { put(it.name.trim(), it.times.toWeekJsonObject()) }
}

private fun runtimeDataDir(homeDir: File): File = File(homeDir, "data")

private fun fileBrowserStateFile(homeDir: File): File = File(homeDir, "file_browser_path.txt")

private fun resolveExistingManagedDir(rootDir: File, candidate: File): File {
    var current = candidate
    while (true) {
        if (current.exists() && current.isDirectory && current.absolutePath.startsWith(rootDir.absolutePath)) {
            return current
        }
        val parent = current.parentFile ?: return rootDir
        if (!parent.absolutePath.startsWith(rootDir.absolutePath)) return rootDir
        if (current == rootDir) return rootDir
        current = parent
    }
}

private fun loadSavedFileBrowserDir(homeDir: File, rootDir: File): File {
    val saved = runCatching { fileBrowserStateFile(homeDir).readText(Charsets.UTF_8).trim() }.getOrDefault("")
    if (saved.isBlank()) return rootDir
    return resolveExistingManagedDir(rootDir, File(saved))
}

private fun saveFileBrowserDir(homeDir: File, rootDir: File, currentDir: File) {
    val resolved = resolveExistingManagedDir(rootDir, currentDir)
    runCatching {
        fileBrowserStateFile(homeDir).writeText(resolved.absolutePath, Charsets.UTF_8)
    }
}

private fun organizeRuntimeFiles(homeDir: File) {
    runtimeDataDir(homeDir).mkdirs()
    qrDir(homeDir).mkdirs()
    cookieDir(homeDir).mkdirs()
    tokenDir(homeDir).mkdirs()
    fileDir(homeDir).mkdirs()
}

private fun pendingQrFiles(homeDir: File): List<File> {
    return qrDir(homeDir).listFiles()
        ?.filter { it.isFile && it.name.startsWith("qrcode_") && it.name.endsWith(".jpg") }
        ?.sortedByDescending { it.lastModified() }
        ?: emptyList()
}

private fun managedFiles(homeDir: File): List<File> {
    return homeDir.listFiles()
        ?.asList()
        ?.sortedWith(compareBy<File>({ !it.isDirectory }, { it.name.lowercase(Locale.ROOT) }))
        ?: emptyList()
}

private fun deleteManagedEntry(file: File) {
    runCatching {
        if (file.isDirectory) file.deleteRecursively() else file.delete()
    }
}

private fun qrOwnerName(file: File): String {
    return file.name.removePrefix("qrcode_").removeSuffix(".jpg")
}

private fun deleteUserCookieFiles(homeDir: File, name: String) {
    val safe = sanitizeForFileName(name)
    listOf(
        File(cookieDir(homeDir), "cookie_${safe}.txt"),
        File(qrDir(homeDir), "qrcode_${safe}.jpg"),
    ).forEach {
        if (it.exists()) it.delete()
    }
}

private fun deleteServiceTokenFiles(homeDir: File, name: String) {
    val safe = sanitizeForFileName(name)
    listOf(
        File(tokenDir(homeDir), "access_token_wx_${safe}.txt"),
        File(tokenDir(homeDir), "access_token_dd_${safe}.txt"),
        File(tokenDir(homeDir), "access_token_fs_${safe}.txt"),
    ).forEach {
        if (it.exists()) it.delete()
    }
}

private fun shareManagedFile(context: Context, file: File, title: String) {
    if (!file.exists() || !file.isFile) return
    val sharedDir = File(context.cacheDir, "shared").apply { mkdirs() }
    val target = File(sharedDir, file.name)
    FileInputStream(file).use { input ->
        FileOutputStream(target).use { output -> input.copyTo(output) }
    }
    val uri: Uri = FileProvider.getUriForFile(context, "cn.yuketang.runner.fileprovider", target)
    val intent = Intent(Intent.ACTION_SEND).apply {
        type = mimeTypeFor(file)
        putExtra(Intent.EXTRA_STREAM, uri)
        putExtra(Intent.EXTRA_SUBJECT, title)
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    context.startActivity(Intent.createChooser(intent, "分享文件"))
}

private fun shareQr(context: Context, file: File, title: String) {
    shareManagedFile(context, file, title)
}

private fun saveManagedFileToDownloads(context: Context, file: File, targetName: String = file.name) {
    if (!file.exists() || !file.isFile) return
    val resolver = context.contentResolver
    val values = ContentValues().apply {
        put(MediaStore.Downloads.DISPLAY_NAME, targetName)
        put(MediaStore.Downloads.MIME_TYPE, mimeTypeFor(file))
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)
        }
    }
    val uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values) ?: return
    resolver.openOutputStream(uri)?.use { output ->
        FileInputStream(file).use { input -> input.copyTo(output) }
    }
}

private fun saveQrToDownloads(context: Context, file: File, title: String) {
    saveManagedFileToDownloads(context, file, "qrcode_${sanitizeForFileName(title)}.jpg")
}

private fun JSONObject?.toMutableWeekTimeList() = mutableStateListOf<WeekTimeEntry>().apply {
    if (this@toMutableWeekTimeList != null) {
        val keys = this@toMutableWeekTimeList.keys().asSequence().toList().sortedBy { it.toIntOrNull() ?: 99 }
        keys.forEach { key ->
            add(WeekTimeEntry(key, this@toMutableWeekTimeList.optString(key, "")))
        }
    }
}

private fun MutableList<WeekTimeEntry>.toWeekJsonObject(): JSONObject = JSONObject().apply {
    this@toWeekJsonObject.filter { it.weekDay.isNotBlank() && it.time.isNotBlank() }
        .forEach { put(it.weekDay, it.time) }
}

private data class ScheduleEntry(
    val name: String,
    val times: SnapshotStateList<WeekTimeEntry>,
)

private data class FileEditorState(
    val file: File,
    val text: TextFieldValue,
)

private data class WeekTimeEntry(
    val weekDay: String,
    val time: String,
)

private const val DEFAULT_CONFIG = """
{
  "yuketang": {
    "users": [],
    "timeout": 30
  },
  "send": {
    "services": [],
    "threads": 5,
    "timeout": 30
  },
  "llm": {
    "models": [],
    "threads": 5,
    "timeout": 60
  },
  "util": {
    "threads": 10,
    "timeout": 30,
    "timezone": "Asia/Shanghai"
  }
}
"""
