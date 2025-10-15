# Setting up Mahoraga MCP with Claude Code

## Step 1: Install Dependencies

```bash
cd /Users/abhinavsai/POC/mahoraga-mac/mahoraga-mcp
pip install -e .
```

## Step 2: Add MCP Server to Claude Code

Run this command to add the Mahoraga MCP server:

```bash
claude mcp add mahoraga python3 /Users/abhinavsai/POC/mahoraga-mac/mahoraga-mcp/server.py
```

Verify it's connected:
```bash
claude mcp list
```

You should see: `mahoraga: ... - ✓ Connected`

## Step 3: Verify Installation

In Claude Code, you should now see 4 new tools available:
- `mahoraga__build`
- `mahoraga__connect`
- `mahoraga__configure`
- `mahoraga__execute`

## Step 4: First Time Usage

### 4.1 Setup Dependencies
```
Setup my system for Mahoraga mobile testing
```
This will:
- Check Python version
- Install ADB if missing
- Install Mahoraga package
- Verify Portal APK

### 4.2 Connect Device
Make sure you have an Android emulator running or device connected, then:
```
Connect to my Android device
```

### 4.3 Configure Agent
```
Configure Mahoraga with:
- API key: sk-or-YOUR_KEY_HERE
- Model: openai/gpt-4o
- Enable vision
- Enable reasoning
```

### 4.4 Run Your First Test
```
Execute this task: Open Settings and navigate to About Phone
```

## Example Session

```
You: "I want to test my Android app with Mahoraga"

Claude: "I'll help you set up Mahoraga for mobile testing. Let me start by
        checking if your system has all the required dependencies."
        [calls mahoraga__build]

You: "Great! Now connect to my emulator"

Claude: [calls mahoraga__connect with no device_serial to auto-detect]

You: "Configure it to use Claude 3.5 Sonnet with vision enabled.
      My API key is sk-or-..."

Claude: [calls mahoraga__configure with the settings]

You: "Now open Instagram and navigate to the profile page"

Claude: [calls mahoraga__execute with live streaming of the execution]
```

## Troubleshooting

### Tools not showing up
- Make sure you've restarted Claude Code completely
- Check the config file path is correct for your OS
- Verify the server.py path is absolute and correct

### "No device found" error
- Start Android Studio emulator
- Or connect physical device with USB debugging enabled
- Run `adb devices` in terminal to verify device is visible

### "Portal not ready" error
- The `connect` tool will automatically try to install it
- If it fails, manually run: `mahoraga setup --device <serial>`

### API key errors
- Make sure you've run `configure` with a valid OpenRouter API key
- Key should start with `sk-or-`

## Advanced Usage

### Using with multiple devices
```
Connect to device emulator-5556
```

### Adjusting execution parameters
```
Configure with max_steps: 25 and reasoning: true
```

### Debug mode
```
Configure with debug: true
```

This will show verbose logs during execution.

## Next Steps

Once you've verified everything works:
1. Test with your own Android apps
2. Create reusable test scenarios
3. Explore reasoning and reflection modes for complex tasks
4. Consider hosting the MCP server for team access