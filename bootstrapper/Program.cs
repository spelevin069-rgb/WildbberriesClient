using System.Diagnostics;
using System.IO.Compression;
using System.Net.Http.Headers;
using System.Text.Json;

// Set this to the public GitHub repository that publishes the release assets.
const string GitHubRepository = "YOUR_GITHUB_USERNAME/WildbberriesClient";
const string BundleAssetName = "WildbberriesClient-Bundle.zip";

Console.Title = "WildbberriesClient Installer";
Console.WriteLine("========================================");
Console.WriteLine("       WildbberriesClient Installer     ");
Console.WriteLine("========================================\n");

if (GitHubRepository.StartsWith("YOUR_", StringComparison.Ordinal))
{
    Console.WriteLine("GitHub repository is not configured yet.");
    Console.WriteLine("Edit GitHubRepository in bootstrapper/Program.cs, then publish again.");
    Console.WriteLine("Example: myname/WildbberriesClient");
    Console.ReadKey();
    return;
}

string installDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "WildbberriesClient");
string tempDir = Path.Combine(Path.GetTempPath(), "WildbberriesClient-" + Guid.NewGuid().ToString("N"));
string bundlePath = Path.Combine(tempDir, BundleAssetName);
Directory.CreateDirectory(tempDir);

try
{
    using var http = new HttpClient();
    http.DefaultRequestHeaders.UserAgent.Add(new ProductInfoHeaderValue("WildbberriesClientInstaller", "1.0"));
    http.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/vnd.github+json"));

    Console.WriteLine("Checking the latest GitHub release...");
    string api = $"https://api.github.com/repos/{GitHubRepository}/releases/latest";
    using JsonDocument release = JsonDocument.Parse(await http.GetStringAsync(api));
    var assets = release.RootElement.GetProperty("assets").EnumerateArray();
    string? downloadUrl = null;
    foreach (var asset in assets)
    {
        if (asset.GetProperty("name").GetString() == BundleAssetName)
        {
            downloadUrl = asset.GetProperty("browser_download_url").GetString();
            break;
        }
    }
    if (string.IsNullOrWhiteSpace(downloadUrl))
        throw new Exception($"Asset {BundleAssetName} was not found in the latest GitHub release.");

    Console.WriteLine("Downloading launcher and game client...");
    using (var response = await http.GetAsync(downloadUrl, HttpCompletionOption.ResponseHeadersRead))
    {
        response.EnsureSuccessStatusCode();
        await using var input = await response.Content.ReadAsStreamAsync();
        await using var output = File.Create(bundlePath);
        await input.CopyToAsync(output);
    }

    Console.WriteLine("Preparing installation...");
    string stage = Path.Combine(tempDir, "bundle");
    ZipFile.ExtractToDirectory(bundlePath, stage);
    string payload = Path.Combine(stage, "ClientPayload.zip");
    string launcher = Path.Combine(stage, "WildbberriesClient.exe");
    if (!File.Exists(payload) || !File.Exists(launcher))
        throw new Exception("The downloaded bundle is incomplete.");

    Directory.CreateDirectory(installDir);
    string runDir = Path.Combine(installDir, "run");
    string backup = Path.Combine(tempDir, "run-backup");
    bool hadRun = Directory.Exists(runDir);
    if (hadRun) Directory.Move(runDir, backup);
    try
    {
        ZipFile.ExtractToDirectory(payload, installDir, true);
        File.Copy(launcher, Path.Combine(installDir, "WildbberriesClient.exe"), true);
        string assets = Path.Combine(stage, "assets");
        if (Directory.Exists(assets)) CopyDirectory(assets, Path.Combine(installDir, "assets"));
        string settings = Path.Combine(stage, "launcher-settings.json");
        string settingsTarget = Path.Combine(installDir, "launcher-settings.json");
        if (File.Exists(settings) && !File.Exists(settingsTarget)) File.Copy(settings, settingsTarget);
        if (hadRun)
        {
            if (Directory.Exists(runDir)) Directory.Delete(runDir, true);
            Directory.Move(backup, runDir);
        }
    }
    catch
    {
        if (hadRun && Directory.Exists(backup))
        {
            if (Directory.Exists(runDir)) Directory.Delete(runDir, true);
            Directory.Move(backup, runDir);
        }
        throw;
    }

    string exe = Path.Combine(installDir, "WildbberriesClient.exe");
    CreateDesktopShortcut(exe, Path.Combine(installDir, "assets", "wildbberries.ico"));
    Console.WriteLine("\nInstallation complete. Starting WildbberriesClient...");
    Process.Start(new ProcessStartInfo(exe) { WorkingDirectory = installDir, UseShellExecute = true });
}
catch (Exception ex)
{
    Console.WriteLine("\nInstallation failed: " + ex.Message);
    Console.WriteLine("Check that the GitHub repository is public and has a published release.");
    Console.WriteLine("Press any key to close.");
    Console.ReadKey();
}
finally
{
    try { Directory.Delete(tempDir, true); } catch { }
}

static void CopyDirectory(string source, string destination)
{
    Directory.CreateDirectory(destination);
    foreach (string file in Directory.GetFiles(source))
        File.Copy(file, Path.Combine(destination, Path.GetFileName(file)), true);
    foreach (string dir in Directory.GetDirectories(source))
        CopyDirectory(dir, Path.Combine(destination, Path.GetFileName(dir)));
}

static void CreateDesktopShortcut(string exe, string icon)
{
    string desktop = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
    string shortcut = Path.Combine(desktop, "WildbberriesClient.lnk");
    string escapedExe = exe.Replace("'", "''");
    string escapedIcon = icon.Replace("'", "''");
    string escapedShortcut = shortcut.Replace("'", "''");
    string script = "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('" + escapedShortcut + "');" +
                    "$s.TargetPath='" + escapedExe + "';$s.WorkingDirectory='" + Path.GetDirectoryName(exe) + "';" +
                    "if(Test-Path '" + escapedIcon + "'){$s.IconLocation='" + escapedIcon + "'};$s.Save()";
    using var process = Process.Start(new ProcessStartInfo("powershell.exe", "-NoProfile -ExecutionPolicy Bypass -Command \"" + script + "\"")
    { CreateNoWindow = true, UseShellExecute = false });
    process?.WaitForExit(10000);
}
