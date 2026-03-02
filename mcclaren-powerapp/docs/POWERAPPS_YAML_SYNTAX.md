# Power Apps Canvas YAML Syntax Guide

Comprehensive reference for building Power Apps Canvas apps using PAC CLI and VS Code.  
**Last Updated**: February 2026 (McLaren Personalisation App project)

---

## Table of Contents

1. [Mandatory Workflow Rules](#mandatory-workflow-rules)
2. [Quick Start Workflow](#quick-start-workflow)
3. [PAC CLI Commands](#pac-cli-commands-reference)
4. [Working Control Types](#working-control-types)
5. [Controls That Don't Work](#control-types-that-do-not-work)
6. [Syntax Rules](#syntax-rules)
7. [Common Patterns](#common-patterns)
8. [App.fx.yaml Global Setup](#appfxyaml-global-setup)
9. [Screen Templates](#screen-templates)
10. [Background Images](#background-images)
11. [Navigation](#navigation)
12. [Layout Tips](#layout-tips)
13. [Common Errors](#common-errors)
14. [App Checker Categories](#app-checker-categories-after-import)
15. [Best Practices](#best-practices)

---

## MANDATORY WORKFLOW RULES

1. **Always validate before packing**: `pac canvas validate --directory "folder"`
2. **Fix ALL validation errors** before running `pac canvas pack`
3. **Test in Power Apps Studio** after every import
4. **Keep changes incremental** - small edits, validate, pack, test, repeat
5. **Control names must be globally unique** - prefix with screen name (e.g., `ClimateBackBtn`, `SeatingBackBtn`)

---

## Quick Start Workflow

```powershell
# 1. Create blank Canvas app in Power Apps Studio first (required starting point)

# 2. Download it
pac canvas download --name "YourAppName" --file-name "app.msapp"

# 3. Unpack to source files
pac canvas unpack --msapp "app.msapp" --sources "app-source"

# 4. Edit YAML files in VS Code (see syntax below)

# 5. ALWAYS validate before packing
pac canvas validate --directory ".\app-source"

# 6. Pack to .msapp (note: --sources not --directory)
pac canvas pack --sources ".\app-source" --msapp "updated.msapp"

# 7. Import via Power Apps Studio: File → Open → Browse
```

### File Format Notes

| Format | Extension | Folder | Notes |
|--------|-----------|--------|-------|
| Current | `.pa.yaml` | `src/` | Full IntelliSense, recommended for new apps |
| Legacy | `.fx.yaml` | `Src/` | Version 0.24, still works but limited support |

**Tip**: If unpacking an existing app creates both formats, you can work with either. The `.fx.yaml` format is simpler but `pac canvas validate` only fully validates `.pa.yaml` files.

---

## PAC CLI Commands Reference

| Command | Purpose |
|---------|---------|
| `pac auth create` | Authenticate to Power Platform |
| `pac auth list` | List auth profiles |
| `pac auth select --index N` | Switch active environment |
| `pac canvas list` | List Canvas apps in environment |
| `pac canvas download --name "App" --file-name "app.msapp"` | Download app package |
| `pac canvas unpack --msapp "app.msapp" --sources "folder"` | Extract to YAML source |
| `pac canvas validate --directory "folder"` | Validate source before pack |
| `pac canvas pack --sources "folder" --msapp "output.msapp"` | Compile source to package |

---

## Working Control Types

These control types reliably work with `pac canvas pack`:

| Type | Usage | Key Properties |
|------|-------|----------------|
| `screen` | Top-level container | `Fill` |
| `label` | Text display OR background cards | `Text`, `Fill`, `Color`, `Font`, `Size`, `FontWeight`, `Align` |
| `button` | Clickable with OnSelect | `Text`, `Fill`, `Color`, `OnSelect`, `BorderColor`, `BorderThickness` |
| `slider` | Numeric value selection | `Min`, `Max`, `Default` (must be numeric!), `ValueFill`, `HandleFill`, `RailFill` |
| `image` | Images/backgrounds | `Image` (URL string), `ImagePosition`, `Transparency` |

---

## Control Types That DO NOT Work

These cause import errors or formula issues - add them manually in Power Apps Studio after import:

| Type | Why It Fails | Alternative |
|------|--------------|-------------|
| `radio` | Invalid control type | Use buttons with conditional Fill to show selection state |
| `toggle` | Invalid control type | Use button with variable to track on/off |
| `dropdown` / `dropDown` | Schema issues | Add in Studio UI |
| `text_input` / `textInput` | Property conflicts | Add in Studio UI |
| `container` | Nesting issues | Use labels with `Fill` as visual card backgrounds |

---

## Syntax Rules

### Basic Property Format
```yaml
ControlName As controlType:
    PropertyName: =Value
    PropertyName: ="String value"
    PropertyName: =FormulaExpression
```

### Color Values
```yaml
# CORRECT - RGBA or Color enum
Fill: =RGBA(0, 0, 0, 1)           # Solid black
Fill: =RGBA(0, 0, 0, 0)           # Fully transparent
Fill: =Color.Transparent          # Also fully transparent
Fill: =RGBA(255, 128, 0, 1)       # McLaren Orange

# WRONG - bare Transparent keyword
Fill: =Transparent                 # ERROR: "Name isn't valid"
```

### If() Function - CRITICAL Rule
```yaml
# CORRECT - full RGBA literal values in If()
Fill: =If(varDriveMode = "Sport", RGBA(255, 128, 0, 1), RGBA(26, 26, 26, 1))

# WRONG - variable references inside If()
Fill: =If(varDriveMode = "Sport", McLarenOrange, McLarenDarkGrey)
# ERROR: Variables from App.OnStart cannot resolve in If() during initial render
```

### OnSelect - Single Statement Only
```yaml
# CORRECT - single statement
OnSelect: =Notify("Saved!", NotificationType.Success)

# CORRECT - single Set()
OnSelect: =Set(varDriveMode, "Sport")

# CORRECT - single Navigate()
OnSelect: =Navigate(ClimateScreen, ScreenTransition.Fade)

# WRONG - semicolon chaining causes "Incompatible type" errors
OnSelect: =Set(varValue, 50); Notify("Saved!", NotificationType.Success)

# WRONG - multiline block format also fails
OnSelect: |-
    =Set(varValue, 50);
    Notify("Saved!")
```

**Workaround**: For complex OnSelect logic, keep YAML simple with just `Notify()` or `Navigate()`, then add the rest in Power Apps Studio after import.

### Slider Default - Must Be Numeric
```yaml
# CORRECT
Default: =50
Default: =varTemperature    # OK if varTemperature is a number

# WRONG - string values cause conversion errors
Default: ="Medium"          # ERROR: "value 'Medium' cannot be converted"
```

### Multiline Text in Labels
```yaml
# Use Char(10) for newlines
Text: ="Line 1" & Char(10) & "Line 2" & Char(10) & "Line 3"

# Example with variables
Text: ="Temp: " & Text(varTemperature, "0") & "C" & Char(10) & "Mode: " & varDriveMode
```

---

## Common Patterns

### Label as Background Card
Use labels with `Fill` and empty `Text` as visual card backgrounds:

```yaml
    CardBackground As label:
        Fill: =RGBA(26, 26, 26, 1)
        Height: =130
        Text: =""
        Width: =350
        X: =40
        Y: =300
        ZIndex: =10

    CardTitle As label:
        Color: =RGBA(255, 128, 0, 1)
        Font: =Font.'Segoe UI'
        FontWeight: =FontWeight.Bold
        Height: =25
        Size: =12
        Text: ="CLIMATE"
        Width: =330
        X: =50
        Y: =310
        ZIndex: =11

    CardContent As label:
        Color: =RGBA(192, 192, 192, 1)
        Font: =Font.'Segoe UI'
        Height: =80
        Size: =11
        Text: ="Temperature: 22C" & Char(10) & "Heated Seats: On"
        Width: =330
        X: =50
        Y: =335
        ZIndex: =12
```

### Button Selection State (Radio Alternative)
```yaml
    ComfortBtn As button:
        BorderColor: =RGBA(255, 128, 0, 1)
        BorderThickness: =2
        Color: =RGBA(255, 255, 255, 1)
        Fill: =If(varDriveMode = "Comfort", RGBA(255, 128, 0, 1), RGBA(26, 26, 26, 1))
        Height: =60
        OnSelect: =Set(varDriveMode, "Comfort")
        Text: ="COMFORT"
        Width: =200
        X: =100
        Y: =200
        ZIndex: =5

    SportBtn As button:
        BorderColor: =RGBA(255, 128, 0, 1)
        BorderThickness: =2
        Color: =RGBA(255, 255, 255, 1)
        Fill: =If(varDriveMode = "Sport", RGBA(255, 128, 0, 1), RGBA(26, 26, 26, 1))
        Height: =60
        OnSelect: =Set(varDriveMode, "Sport")
        Text: ="SPORT"
        Width: =200
        X: =320
        Y: =200
        ZIndex: =6
```

---

## App.fx.yaml Global Setup

Define colors and variables in App.OnStart for consistency:

```yaml
App As appinfo:
    OnStart: |-
        =// Brand Colors
        Set(McLarenOrange, RGBA(255, 128, 0, 1));
        Set(McLarenBlack, RGBA(0, 0, 0, 1));
        Set(McLarenDarkGrey, RGBA(26, 26, 26, 1));
        Set(McLarenSilver, RGBA(192, 192, 192, 1));
        Set(McLarenWhite, RGBA(255, 255, 255, 1));

        // Demo Customer Data
        Set(CurrentCustomer, {
            Name: "James Harrison",
            CustomerId: "MCL-2026-0472",
            Vehicle: "750S Spider",
            VehicleSpec: "Volcanic Red"
        });

        // Default Settings (numeric values for sliders)
        Set(varTemperature, 22);
        Set(varSeatPosition, 45);
        Set(varBassLevel, 4);
        Set(varDriveMode, "Sport");
        Set(varHeatedSeats, "Medium");
        Set(varLaunchControl, true)
```

**Remember**: Variables like `McLarenOrange` work in direct property assignments (`Fill: =McLarenOrange`) but NOT inside `If()` functions. Use literal RGBA values in `If()`.

---

## Screen Templates

### Basic Screen with Back Button
```yaml
MyScreen As screen:
    Fill: =McLarenBlack

    MyScreenBackBtn As button:
        BorderColor: =RGBA(255, 128, 0, 1)
        BorderThickness: =2
        Color: =RGBA(255, 255, 255, 1)
        Fill: =Color.Transparent
        Font: =Font.'Segoe UI'
        Height: =50
        OnSelect: =Navigate(HomeScreen, ScreenTransition.Fade)
        Text: ="< BACK"
        Width: =120
        X: =20
        Y: =15
        ZIndex: =1

    MyScreenTitle As label:
        Align: =Align.Center
        Color: =RGBA(255, 128, 0, 1)
        Font: =Font.'Segoe UI'
        FontWeight: =FontWeight.Bold
        Height: =40
        Size: =24
        Text: ="MY SCREEN TITLE"
        Width: =400
        X: =Parent.Width / 2 - Self.Width / 2
        Y: =20
        ZIndex: =2
```

---

## Background Images

Add subtle background images using the `image` control type:

```yaml
    BackgroundImage As image:
        Height: =Parent.Height
        Image: ="https://example.com/background.jpg"
        ImagePosition: =ImagePosition.Fill
        Transparency: =0.82
        Width: =Parent.Width
        X: =0
        Y: =0
        ZIndex: =0
```

### Key Properties
| Property | Values | Notes |
|----------|--------|-------|
| `Image` | `="URL"` | Must be publicly accessible URL |
| `ImagePosition` | `ImagePosition.Fill`, `.Fit`, `.Center`, `.Stretch` | Fill covers entire area |
| `Transparency` | `0` to `1` | 0 = fully visible, 0.82 = 18% visible (subtle), 1 = invisible |

### Recommended Transparency Values
| Effect | Value |
|--------|-------|
| Very subtle hint | `0.90` - `0.95` |
| Subtle background | `0.80` - `0.85` |
| Visible but not distracting | `0.70` - `0.75` |
| Prominent | `0.50` - `0.60` |

**Important**: 
- Use `ZIndex: =0` to position behind all other controls
- URL must be publicly accessible (Azure Blob, public CDN, etc.)
- External URLs from some sites may be blocked by CORS

---

## Navigation

### Navigate Between Screens
```yaml
OnSelect: =Navigate(TargetScreen, ScreenTransition.Fade)
```

### Available Transitions
- `ScreenTransition.Fade`
- `ScreenTransition.Cover`
- `ScreenTransition.UnCover`
- `ScreenTransition.CoverRight`
- `ScreenTransition.UnCoverRight`
- `ScreenTransition.None`

### Navigation Tile Pattern
```yaml
    ClimateTile As button:
        BorderColor: =RGBA(255, 128, 0, 1)
        BorderThickness: =2
        Color: =RGBA(255, 255, 255, 1)
        Fill: =RGBA(26, 26, 26, 1)
        Font: =Font.'Segoe UI'
        FontWeight: =FontWeight.Bold
        Height: =55
        OnSelect: =Navigate(ClimateScreen, ScreenTransition.Fade)
        Size: =11
        Text: ="CLIMATE"
        Width: =200
        X: =133
        Y: =190
        ZIndex: =7
```

---

## Layout Tips

### Default Canvas Size
- **DesktopOrTablet**: 1366 x 768 pixels
- **Phone**: 640 x 1136 pixels

### Centering Elements Horizontally
```yaml
X: =Parent.Width / 2 - Self.Width / 2
# OR for fixed width controls
X: =(Parent.Width - 400) / 2    # Centers a 400px wide control
```

### Grid Layout (5 tiles across)
For 1366px width with margins:
```yaml
# Tile 1: X: =133
# Tile 2: X: =358   (133 + 200 + 25 gap)
# Tile 3: X: =583
# Tile 4: X: =808
# Tile 5: X: =1033
# Width: 200 each, 25px gaps, 133px margins
```

### ZIndex Rules
- `0` = Background images (behind everything)
- `1+` = Main content (ascending order)
- Higher ZIndex = rendered on top

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| PA3008 | Duplicate control names | Prefix controls with screen name: `ClimateBackBtn`, `SeatingBackBtn` |
| Import fails silently | Invalid control types | Use only `label`, `button`, `slider`, `image` |
| "Name isn't valid. 'Transparent'" | Bare `Transparent` keyword | Use `Color.Transparent` or `RGBA(0,0,0,0)` |
| "The function 'If' has some invalid arguments" | Variables in If() | Use literal RGBA values, not variable names |
| "Incompatible type" on OnSelect | Semicolon-chained statements | Use SINGLE statement only; add logic in Studio |
| "value 'X' cannot be converted" | String in slider Default | Slider Default must be numeric (50, not "Medium") |
| Checksum mismatch warning | Normal after edits | Safe to ignore - this is expected |
| Image not loading | URL not accessible | Use publicly hosted image URL; check CORS |

---

## App Checker Categories (After Import)

Power Apps Studio App Checker shows these categories:

| Category | Blocking? | Action |
|----------|-----------|--------|
| **Formulas** | YES | Fix in YAML before import |
| **Runtime** | YES | Fix in YAML before import |
| **Accessibility** | No | Optional - add `AccessibleLabel`, `TabIndex` in Studio |
| **Performance** | No | Optional - tips for optimization |
| **Data source** | Maybe | Check connections in Studio |

**For demos**: Accessibility/Performance warnings are acceptable. Only Formula/Runtime errors need fixing.

---

## Best Practices

### Development Workflow
1. **Small incremental changes** - edit 1-2 controls, validate, pack, test
2. **Validate after every change** - catches errors early
3. **Use unique control names** - prefix with screen name
4. **Keep OnSelect simple** - single statements only; complex logic in Studio
5. **Test after every import** - don't batch too many changes

### Code Organization
1. **App.fx.yaml** - global colors, customer data, default variable values
2. **One file per screen** - `HomeScreen.fx.yaml`, `ClimateScreen.fx.yaml`, etc.
3. **Alphabetical properties** - PAC tools will sort them anyway
4. **Sequential ZIndex** - start at 0 for backgrounds, 1+ for content

### What to Do in YAML vs Studio

| Task | YAML | Studio |
|------|------|--------|
| Screen structure & layout | ✅ | |
| Labels, buttons, sliders | ✅ | |
| Background images | ✅ | |
| Simple navigation | ✅ | |
| Color theming | ✅ | |
| Radio/Toggle/Dropdown | | ✅ |
| Complex OnSelect logic | | ✅ |
| Data connections | | ✅ |
| Accessibility properties | | ✅ |
| Fine-tuning positions | | ✅ |

---

## CanvasManifest.json

If adding new screens, update the ScreenOrder array:

```json
{
  "ScreenOrder": [
    "HomeScreen",
    "ClimateScreen",
    "SeatingScreen",
    "AudioScreen",
    "DrivingScreen",
    "DisplayScreen"
  ]
}
```

---

## Quick Reference Card

```yaml
# Screen with background image
MyScreen As screen:
    Fill: =RGBA(0, 0, 0, 1)

    BackgroundImg As image:
        Height: =Parent.Height
        Image: ="https://example.com/bg.jpg"
        ImagePosition: =ImagePosition.Fill
        Transparency: =0.82
        Width: =Parent.Width
        X: =0
        Y: =0
        ZIndex: =0

    BackBtn As button:
        BorderColor: =RGBA(255, 128, 0, 1)
        BorderThickness: =2
        Color: =RGBA(255, 255, 255, 1)
        Fill: =Color.Transparent
        Height: =50
        OnSelect: =Navigate(HomeScreen, ScreenTransition.Fade)
        Text: ="< BACK"
        Width: =120
        X: =20
        Y: =15
        ZIndex: =1

    Title As label:
        Align: =Align.Center
        Color: =RGBA(255, 128, 0, 1)
        FontWeight: =FontWeight.Bold
        Height: =40
        Size: =24
        Text: ="TITLE"
        Width: =Parent.Width
        Y: =20
        ZIndex: =2

    CardBg As label:
        Fill: =RGBA(26, 26, 26, 1)
        Height: =120
        Text: =""
        Width: =300
        X: =40
        Y: =100
        ZIndex: =3

    ValueSlider As slider:
        Default: =50
        HandleFill: =RGBA(255, 255, 255, 1)
        Height: =40
        Max: =100
        Min: =0
        ValueFill: =RGBA(255, 128, 0, 1)
        Width: =260
        X: =60
        Y: =160
        ZIndex: =4
```

---

## Version History

| Date | Changes |
|------|---------|
| Feb 2026 | Added image control, background patterns, transparency guide, navigation tiles, layout tips, comprehensive error table, card patterns, quick reference |
| Jan 2026 | Initial guide with basic controls and syntax rules |
