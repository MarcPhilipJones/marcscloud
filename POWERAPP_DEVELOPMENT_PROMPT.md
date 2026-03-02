# Power Apps Canvas Development with VS Code & AI

*Copy this document into your `.github/copilot-instructions.md` or use as a system prompt to teach Claude (Opus 4.5+) how to build Power Apps Canvas apps directly in VS Code using YAML.*

---

## What This Enables

You can build **fully functional Power Apps Canvas apps** using only:
- VS Code (any text editor)
- PAC CLI (Power Platform CLI)
- AI assistant (Claude/Copilot)

No need to use Power Apps Studio for initial development. Design your entire app in YAML, then import the finished product.

---

## Prerequisites

### Install Power Platform CLI (PAC)
```powershell
# Option 1: Via winget (Windows)
winget install Microsoft.PowerPlatformCLI

# Option 2: Via npm (cross-platform)
npm install -g pac-cli

# Option 3: Download from Microsoft
# https://aka.ms/PowerAppsCLI
```

### Verify Installation
```powershell
pac --version
# Should show version like: 1.32.x
```

### Authenticate to Power Platform
```powershell
# Interactive login
pac auth create

# Or specify environment
pac auth create --environment "https://yourorg.crm4.dynamics.com"

# List and select auth profiles
pac auth list
pac auth select --index 1
```

---

## CRITICAL WORKFLOW RULES

1. **Always validate before packing**: `pac canvas validate --directory "folder"`
2. **Fix ALL validation errors** before running `pac canvas pack`
3. **Test in Power Apps Studio** after every import
4. **Keep changes incremental** - small edits, validate, pack, test, repeat
5. **Control names must be globally unique** - prefix with screen name (e.g., `ClimateBackBtn`, `SeatingBackBtn`)

---

## PAC CLI Commands Reference

```powershell
# Authenticate to Power Platform
pac auth create

# List auth profiles and switch environment
pac auth list
pac auth select --index 1

# List Canvas apps in environment
pac canvas list

# Download existing app
pac canvas download --name "MyApp" --file-name "app.msapp"

# Unpack to YAML source files
pac canvas unpack --msapp "app.msapp" --sources "app-source"

# ALWAYS validate before packing
pac canvas validate --directory ".\app-source"

# Pack YAML back to .msapp
pac canvas pack --sources ".\app-source" --msapp "updated.msapp"

# Import via Power Apps Studio: File → Open → Browse
```

---

## Project Structure

```
my-powerapp/
├── src/
│   ├── App.pa.yaml              # App-level config, OnStart, global variables
│   ├── CanvasManifest.json      # App metadata, screen order
│   └── screens/
│       ├── HomeScreen.pa.yaml   # One file per screen
│       ├── SettingsScreen.pa.yaml
│       └── DetailScreen.pa.yaml
├── docs/
│   └── POWERAPPS_YAML_SYNTAX.md # This reference guide
└── README.md
```

---

## App.pa.yaml - Global Setup

Define brand colors and global variables in `App.OnStart`:

```yaml
App As appinfo:
  BackEnabled: =false
  StartScreen: =HomeScreen
  
  OnStart: |
    =// Brand Colors - define once, use everywhere
    Set(BrandPrimary, ColorValue("#FF8000"));
    Set(BrandBlack, ColorValue("#000000"));
    Set(BrandDarkGrey, ColorValue("#1A1A1A"));
    Set(BrandSilver, ColorValue("#C0C0C0"));
    Set(BrandWhite, ColorValue("#FFFFFF"));
    
    // User context
    Set(CurrentUser, {
        Name: "John Smith",
        UserId: "USR-2026-0001",
        Role: "Administrator"
    });
    
    // Default settings (use numeric values for sliders)
    Set(AppSettings, {
        Theme: "Dark",
        Volume: 50,
        Notifications: true
    })
```

---

## CanvasManifest.json

```json
{
  "FormatVersion": "1.0.0",
  "MainApp": "App.pa.yaml",
  "Properties": {
    "Name": "My Application",
    "Author": "Your Name",
    "Id": "my-application-id",
    "AppVersion": "1.0.0",
    "Description": "Description of your app",
    "DocumentAppType": "DesktopOrTablet"
  },
  "ScreenOrder": [
    "HomeScreen",
    "SettingsScreen",
    "DetailScreen"
  ]
}
```

---

## WORKING Control Types

These control types reliably work with `pac canvas pack`:

| Type | Usage | Key Properties |
|------|-------|----------------|
| `screen` | Top-level container | `Fill` |
| `label` | Text display AND background cards | `Text`, `Fill`, `Color`, `Size`, `FontWeight`, `Align` |
| `button` | Clickable with OnSelect | `Text`, `Fill`, `Color`, `OnSelect`, `BorderColor`, `BorderThickness`, `BorderRadius` |
| `slider` | Numeric value selection | `Min`, `Max`, `Default` (MUST be numeric!), `ValueFill`, `HandleFill`, `RailFill` |
| `image` | Images/backgrounds | `Image` (URL string), `ImagePosition`, `Transparency` |
| `icon` | Built-in icons | `Icon`, `Color` |
| `container` | Layout grouping | `X`, `Y`, `Width`, `Height`, `Fill` |
| `circle` | Circular shapes | `Fill`, `Width`, `Height` |

---

## Control Types That DO NOT WORK in YAML

Add these manually in Power Apps Studio AFTER import:

| Type | Why It Fails | Alternative |
|------|--------------|-------------|
| `radio` | Invalid control type | Use buttons with conditional Fill to show selection state |
| `toggle` | Invalid control type | Use button with variable to track on/off |
| `dropdown` / `dropDown` | Schema issues | Add in Studio UI |
| `text_input` / `textInput` | Property conflicts | Add in Studio UI |
| `gallery` | Complex binding issues | Add in Studio UI |

---

## Syntax Rules - READ CAREFULLY

### Basic Property Format
```yaml
ControlName As controlType:
  PropertyName: =Value
  PropertyName: ="String value"
  PropertyName: =FormulaExpression
```

### Color Values - CORRECT vs WRONG
```yaml
# CORRECT - RGBA, ColorValue, or Color enum
Fill: =RGBA(0, 0, 0, 1)              # Solid black
Fill: =RGBA(0, 0, 0, 0)              # Fully transparent
Fill: =Color.Transparent             # Also fully transparent
Fill: =ColorValue("#FF8000")         # Hex color

# WRONG - bare Transparent keyword
Fill: =Transparent                   # ERROR: "Name isn't valid"
```

### If() Function - CRITICAL RULE
```yaml
# CORRECT - use literal RGBA values in If()
Fill: =If(varMode = "Active", RGBA(255, 128, 0, 1), RGBA(26, 26, 26, 1))

# WRONG - variable references inside If()
Fill: =If(varMode = "Active", BrandPrimary, BrandDarkGrey)
# ERROR: Variables from App.OnStart cannot resolve in If() during initial render
```

### OnSelect - SINGLE Statement Only
```yaml
# CORRECT - single statement
OnSelect: =Notify("Saved!", NotificationType.Success)
OnSelect: =Set(varMode, "Sport")
OnSelect: =Navigate(SettingsScreen, ScreenTransition.Fade)

# WRONG - semicolon chaining causes errors
OnSelect: =Set(varValue, 50); Notify("Saved!", NotificationType.Success)
```

**Workaround**: Keep YAML OnSelect simple with just one statement. Add complex multi-statement logic in Power Apps Studio after import.

### Slider Default - MUST Be Numeric
```yaml
# CORRECT
Default: =50
Default: =AppSettings.Volume

# WRONG - string values cause conversion errors
Default: ="Medium"   # ERROR: "value 'Medium' cannot be converted"
```

### Multiline Text in Labels
```yaml
# Use Char(10) for newlines
Text: ="Line 1" & Char(10) & "Line 2" & Char(10) & "Line 3"
```

---

## Common Patterns

### Screen with Header and Back Button
```yaml
MyScreen As screen:
  Fill: =BrandBlack
  
  HeaderContainer As container:
    X: =0
    Y: =0
    Width: =Parent.Width
    Height: =80
    Fill: =BrandDarkGrey
    
    BackButton As button:
      X: =20
      Y: =15
      Width: =120
      Height: =50
      Text: ="◄ BACK"
      Fill: =Color.Transparent
      Color: =BrandWhite
      OnSelect: =Navigate(HomeScreen, ScreenTransition.Fade)
      BorderColor: =BrandPrimary
      BorderThickness: =2
      BorderRadius: =4
      
    ScreenTitle As label:
      X: =(Parent.Width - 300) / 2
      Y: =20
      Width: =300
      Height: =40
      Text: ="SCREEN TITLE"
      Color: =BrandPrimary
      Size: =22
      FontWeight: =FontWeight.Bold
      Align: =Align.Center
```

### Label as Background Card
Use labels with `Fill` and empty `Text` as visual card backgrounds:

```yaml
  CardBackground As container:
    X: =40
    Y: =120
    Width: =Parent.Width - 80
    Height: =160
    Fill: =BrandDarkGrey
    BorderRadius: =8
    
    CardTitle As label:
      X: =30
      Y: =20
      Width: =300
      Height: =30
      Text: ="CARD TITLE"
      Color: =BrandWhite
      Size: =16
      FontWeight: =FontWeight.Bold
```

### Button Selection State (Radio Alternative)
```yaml
  ComfortBtn As button:
    X: =100
    Y: =200
    Width: =200
    Height: =60
    Text: ="COMFORT"
    BorderColor: =RGBA(255, 128, 0, 1)
    BorderThickness: =2
    Color: =RGBA(255, 255, 255, 1)
    Fill: =If(varMode = "Comfort", RGBA(255, 128, 0, 1), RGBA(26, 26, 26, 1))
    OnSelect: =Set(varMode, "Comfort")

  SportBtn As button:
    X: =320
    Y: =200
    Width: =200
    Height: =60
    Text: ="SPORT"
    BorderColor: =RGBA(255, 128, 0, 1)
    BorderThickness: =2
    Color: =RGBA(255, 255, 255, 1)
    Fill: =If(varMode = "Sport", RGBA(255, 128, 0, 1), RGBA(26, 26, 26, 1))
    OnSelect: =Set(varMode, "Sport")
```

### Slider with Labels
```yaml
  VolumeCard As container:
    X: =40
    Y: =300
    Width: =Parent.Width - 80
    Height: =130
    Fill: =BrandDarkGrey
    BorderRadius: =8
    
    VolumeTitle As label:
      X: =30
      Y: =20
      Width: =200
      Height: =30
      Text: ="VOLUME"
      Color: =BrandWhite
      Size: =16
      FontWeight: =FontWeight.Bold
      
    VolumeValue As label:
      X: =Parent.Width - 100
      Y: =20
      Width: =70
      Height: =30
      Text: =Text(VolumeSlider.Value, "0") & "%"
      Color: =BrandPrimary
      Size: =16
      FontWeight: =FontWeight.Bold
      Align: =Align.Right
      
    VolumeSlider As slider:
      X: =80
      Y: =60
      Width: =Parent.Width - 160
      Height: =50
      Min: =0
      Max: =100
      Default: =50
      ValueFill: =BrandPrimary
      HandleFill: =BrandWhite
      RailFill: =BrandSilver
      ShowValue: =false
      
    MinLabel As label:
      X: =30
      Y: =70
      Width: =50
      Height: =30
      Text: ="MIN"
      Color: =BrandSilver
      Size: =11
      
    MaxLabel As label:
      X: =Parent.Width - 80
      Y: =70
      Width: =50
      Height: =30
      Text: ="MAX"
      Color: =BrandSilver
      Size: =11
```

### Navigation Tile Grid
```yaml
  NavTilesContainer As container:
    X: =40
    Y: =400
    Width: =Parent.Width - 80
    Height: =400
    Fill: =Color.Transparent
    
    SettingsTile As button:
      X: =0
      Y: =0
      Width: =220
      Height: =180
      Text: =""
      Fill: =BrandDarkGrey
      BorderRadius: =8
      OnSelect: =Navigate(SettingsScreen, ScreenTransition.Fade)
      
    SettingsIcon As icon:
      X: =70
      Y: =30
      Width: =80
      Height: =80
      Icon: =Icon.Settings
      Color: =BrandPrimary
      
    SettingsLabel As label:
      X: =0
      Y: =120
      Width: =220
      Height: =40
      Text: ="SETTINGS"
      Color: =BrandWhite
      Size: =18
      FontWeight: =FontWeight.Bold
      Align: =Align.Center
```

---

## Layout Reference

### Default Canvas Sizes
- **DesktopOrTablet**: 1366 x 768 pixels
- **Phone**: 640 x 1136 pixels

### Centering Elements
```yaml
X: =Parent.Width / 2 - Self.Width / 2
# OR for fixed width:
X: =(Parent.Width - 400) / 2    # Centers 400px control
```

### Available Icons
`Icon.Add`, `Icon.Settings`, `Icon.Person`, `Icon.Car`, `Icon.Sunny`, `Icon.Microphone`, `Icon.Lightbulb`, `Icon.Home`, `Icon.ChevronLeft`, `Icon.ChevronRight`, `Icon.Check`, `Icon.Cancel`, etc.

### Navigation Transitions
- `ScreenTransition.Fade`
- `ScreenTransition.Cover`
- `ScreenTransition.UnCover`
- `ScreenTransition.CoverRight`
- `ScreenTransition.None`

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| PA3008 | Duplicate control names | Prefix controls with screen name: `HomeBackBtn`, `SettingsBackBtn` |
| Import fails silently | Invalid control types | Use only working control types (see list above) |
| "Name isn't valid. 'Transparent'" | Bare `Transparent` keyword | Use `Color.Transparent` or `RGBA(0,0,0,0)` |
| "The function 'If' has some invalid arguments" | Variables in If() | Use literal RGBA values, not variable names |
| "Incompatible type" on OnSelect | Semicolon-chained statements | Use SINGLE statement only |
| "value 'X' cannot be converted" | String in slider Default | Slider Default must be numeric |
| Checksum mismatch warning | Normal after edits | Safe to ignore |

---

## Best Practices Summary

### Do in YAML
- Screen structure & layout
- Labels, buttons, sliders, icons, images
- Background containers/cards
- Simple navigation
- Color theming via OnStart variables

### Do in Power Apps Studio (after import)
- Radio buttons, toggles, dropdowns
- Text input controls
- Complex OnSelect logic (multiple statements)
- Data connections
- Galleries
- Accessibility properties

### Development Rhythm
1. Design screen layout in YAML
2. Validate: `pac canvas validate --directory ".\src"`
3. Pack: `pac canvas pack --sources ".\src" --msapp "app.msapp"`
4. Import in Power Apps Studio
5. Add complex controls (radio, dropdown, etc.)
6. Add data connections
7. Test thoroughly
8. Export and commit to source control

---

## How to Get a Packaged .msapp File from AI-Generated YAML

When the AI generates YAML files for you, follow these steps to create an importable Power App:

### Step 1: Create Project Structure
```
my-app/
├── src/
│   ├── App.pa.yaml
│   ├── CanvasManifest.json
│   └── Screens/
│       ├── HomeScreen.pa.yaml
│       └── OtherScreen.pa.yaml
```

### Step 2: Ask AI to Generate Each File
Request each file from the AI:
- "Create the App.pa.yaml with brand colors X, Y, Z"
- "Create the CanvasManifest.json for an app called 'My App'"
- "Create a HomeScreen with navigation tiles for Settings and Profile"

### Step 3: Save Files Locally
Copy each YAML/JSON response from the AI and save to the correct location in your project folder.

### Step 4: Validate the Source
```powershell
cd "path\to\my-app"
pac canvas validate --directory ".\src"
```

Fix any errors reported before proceeding.

### Step 5: Pack to .msapp
```powershell
pac canvas pack --sources ".\src" --msapp ".\my-app.msapp"
```

This creates `my-app.msapp` - a Power Apps package file.

### Step 6: Import into Power Apps Studio
1. Go to https://make.powerapps.com
2. Click **Apps** → **Import canvas app**
3. Browse and select your `.msapp` file
4. Click **Upload** then **Import**

Or open directly:
1. Go to https://make.powerapps.com
2. Click **Create** → **Blank app** → **Blank canvas app**
3. In the app editor: **File** → **Open** → **Browse**
4. Select your `.msapp` file

### Step 7: Add Non-YAML Controls in Studio
After import, manually add:
- Radio buttons
- Dropdown controls
- Text inputs
- Data connections
- Galleries

### Alternative: Ask AI to Provide Ready-to-Copy Commands
You can ask the AI:
> "Give me the complete terminal commands to validate and pack this app"

The AI will provide:
```powershell
# Navigate to project
cd "C:\Projects\my-app"

# Validate
pac canvas validate --directory ".\src"

# Pack (creates .msapp in current folder)
pac canvas pack --sources ".\src" --msapp ".\MyApp.msapp"

# The file MyApp.msapp is now ready to import
```

### Troubleshooting Import Issues

| Problem | Solution |
|---------|----------|
| "Invalid package" | Run `pac canvas validate` and fix all errors first |
| App opens but screens missing | Check `CanvasManifest.json` ScreenOrder array |
| Controls don't appear | Check for invalid control types (radio, toggle, dropdown) |
| Formula errors after import | Check If() uses literal RGBA, not variables |

---

## AI Assistant Instructions

When the user asks you to create Power Apps screens:

1. **Use working control types only**: `screen`, `container`, `label`, `button`, `slider`, `icon`, `image`, `circle`
2. **Never use**: `radio`, `toggle`, `dropdown`, `textInput`, `gallery` in YAML
3. **Always prefix control names** with screen abbreviation for uniqueness
4. **Use literal RGBA values in If()** functions, not variable references
5. **Keep OnSelect to single statements** - no semicolons
6. **Slider Default must be numeric** - never strings
7. **Use `Color.Transparent`** not bare `Transparent`
8. **Suggest adding complex controls in Studio** after import

---

*Last Updated: February 2026*
