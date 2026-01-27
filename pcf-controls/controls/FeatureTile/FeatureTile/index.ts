import { IInputs, IOutputs } from "./generated/ManifestTypes";

/**
 * Fluent UI icon SVG paths (20px regular variants from @fluentui/svg-icons)
 * Using inline SVGs to avoid external dependencies in vanilla PCF
 */
const FLUENT_ICONS: Record<string, string> = {
    // General
    Checkmark: '<path d="M7.03 13.9 3.56 10a.75.75 0 0 0-1.12 1l4 4.5c.29.32.79.34 1.09.03l10-10a.75.75 0 0 0-1.06-1.06L7.03 13.9Z" fill="currentColor"/>',
    Dismiss: '<path d="m4.09 4.22.06-.07a.75.75 0 0 1 .98-.07l.07.07L10 8.94l4.8-4.8a.75.75 0 0 1 1.13.98l-.07.07L11.06 10l4.8 4.8c.27.26.29.68.07.97l-.07.07a.75.75 0 0 1-.97.07l-.07-.07L10 11.06l-4.8 4.8a.75.75 0 0 1-1.13-.98l.07-.07L8.94 10l-4.8-4.8a.75.75 0 0 1-.07-.98l.07-.07-.07.07Z" fill="currentColor"/>',
    Warning: '<path d="M8.68 2.79a1.5 1.5 0 0 1 2.64 0l6.5 12A1.5 1.5 0 0 1 16.5 17h-13a1.5 1.5 0 0 1-1.32-2.21l6.5-12ZM10 7a.75.75 0 0 0-.75.75v3.5a.75.75 0 0 0 1.5 0v-3.5A.75.75 0 0 0 10 7Zm0 8a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z" fill="currentColor"/>',
    Question: '<path d="M10 2a8 8 0 1 1 0 16 8 8 0 0 1 0-16Zm0 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13ZM10 13a1 1 0 1 1 0 2 1 1 0 0 1 0-2Zm0-7.5c1.52 0 2.75 1.23 2.75 2.75 0 .9-.43 1.7-1.1 2.2l-.15.11-.25.17c-.4.29-.5.47-.5.77a.75.75 0 0 1-1.5 0c0-.92.47-1.53 1.15-2.02l.26-.18.1-.07c.33-.24.49-.54.49-.98a1.25 1.25 0 0 0-2.5 0 .75.75 0 0 1-1.5 0C7.25 6.73 8.48 5.5 10 5.5Z" fill="currentColor"/>',
    
    // Home & Building
    Home: '<path d="M10.45 2.24a.75.75 0 0 0-.9 0l-7 5.25A.75.75 0 0 0 2.25 8v8c0 .97.78 1.75 1.75 1.75h3.25a.75.75 0 0 0 .75-.75v-4.5h4v4.5c0 .41.34.75.75.75H16c.97 0 1.75-.78 1.75-1.75V8a.75.75 0 0 0-.3-.6l-7-5.25ZM16.25 8.31V16a.25.25 0 0 1-.25.25h-2.5v-4.5a.75.75 0 0 0-.75-.75h-5.5a.75.75 0 0 0-.75.75v4.5H4a.25.25 0 0 1-.25-.25V8.31L10 3.81l6.25 4.5Z" fill="currentColor"/>',
    Building: '<path d="M6 2a2 2 0 0 0-2 2v14h3v-3.5c0-.28.22-.5.5-.5h5c.28 0 .5.22.5.5V18h3V4a2 2 0 0 0-2-2H6ZM5 18V4a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v14h-2v-3.5c0-.83-.67-1.5-1.5-1.5h-5c-.83 0-1.5.67-1.5 1.5V18H5Zm3-9.5c0-.28.22-.5.5-.5h3c.28 0 .5.22.5.5v1c0 .28-.22.5-.5.5h-3a.5.5 0 0 1-.5-.5v-1Z" fill="currentColor"/>',
    
    // Vehicles & Transport
    Car: '<path d="M6.2 4.5A2.25 2.25 0 0 1 8.32 3h3.36c.9 0 1.73.54 2.1 1.38l.87 1.99c.06.14.15.27.27.37l1.59 1.36c.62.53.99 1.3.99 2.12V14a2 2 0 0 1-2 2h-.75a2 2 0 0 1-2-2H7.25a2 2 0 0 1-2 2H4.5a2 2 0 0 1-2-2v-3.78c0-.81.36-1.59.99-2.12l1.59-1.36c.12-.1.2-.23.27-.37l.86-1.99.02-.04-.03.17Zm6.4 1.1a.75.75 0 0 0-.68-.1h-3.84a.75.75 0 0 0-.68.44L6.55 8h6.9l-.85-2.4ZM4.5 14h.75a.5.5 0 0 0 .5-.5v-.25c0-.14.11-.25.25-.25h8c.14 0 .25.11.25.25v.25c0 .28.22.5.5.5h.75a.5.5 0 0 0 .5-.5v-3.78a.75.75 0 0 0-.28-.58l-.91-.78H5.19l-.91.78a.75.75 0 0 0-.28.58V13.5c0 .28.22.5.5.5Z" fill="currentColor"/>',
    VehicleCar: '<path d="M6.2 4.5A2.25 2.25 0 0 1 8.32 3h3.36c.9 0 1.73.54 2.1 1.38l.87 1.99c.06.14.15.27.27.37l1.59 1.36c.62.53.99 1.3.99 2.12V14a2 2 0 0 1-2 2h-.75a2 2 0 0 1-2-2H7.25a2 2 0 0 1-2 2H4.5a2 2 0 0 1-2-2v-3.78c0-.81.36-1.59.99-2.12l1.59-1.36c.12-.1.2-.23.27-.37l.86-1.99.02-.04-.03.17Zm6.4 1.1a.75.75 0 0 0-.68-.1h-3.84a.75.75 0 0 0-.68.44L6.55 8h6.9l-.85-2.4ZM4.5 14h.75a.5.5 0 0 0 .5-.5v-.25c0-.14.11-.25.25-.25h8c.14 0 .25.11.25.25v.25c0 .28.22.5.5.5h.75a.5.5 0 0 0 .5-.5v-3.78a.75.75 0 0 0-.28-.58l-.91-.78H5.19l-.91.78a.75.75 0 0 0-.28.58V13.5c0 .28.22.5.5.5Z" fill="currentColor"/>',
    
    // Energy & Utilities
    Lightbulb: '<path d="M10 2a5.5 5.5 0 0 0-3 10.1v.4c0 .83.67 1.5 1.5 1.5h3c.83 0 1.5-.67 1.5-1.5v-.4A5.5 5.5 0 0 0 10 2ZM8.5 15h3v.5c0 .28-.22.5-.5.5H9a.5.5 0 0 1-.5-.5V15ZM8 17.5c0-.28.22-.5.5-.5h3c.28 0 .5.22.5.5v.5a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1v-.5ZM10 3.5a4 4 0 0 1 2.12 7.4.75.75 0 0 0-.37.65v.95a.5.5 0 0 1-.5.5h-2.5a.5.5 0 0 1-.5-.5v-.95a.75.75 0 0 0-.37-.64A4 4 0 0 1 10 3.5Z" fill="currentColor"/>',
    Flash: '<path d="M11.1 2.02a.75.75 0 0 1 .52.86L10.56 8H15a.75.75 0 0 1 .6 1.2l-7 9.33a.75.75 0 0 1-1.33-.64l1.08-5.39H4a.75.75 0 0 1-.57-1.24l7-8.17a.75.75 0 0 1 .68-.27ZM5.35 11h4.4a.75.75 0 0 1 .74.88l-.65 3.22 4.52-6.02H9.75a.75.75 0 0 1-.73-.9l.65-3.55L5.35 11Z" fill="currentColor"/>',
    PlugConnected: '<path d="M8.5 2a.5.5 0 0 0-.5.5V6H6.5a.5.5 0 0 0-.5.5v3a4 4 0 0 0 3.5 3.97V17a1 1 0 0 0 1 1 1 1 0 0 0 1-1v-3.53A4 4 0 0 0 15 9.5v-3a.5.5 0 0 0-.5-.5H13V2.5a.5.5 0 0 0-.5-.5h-1a.5.5 0 0 0-.5.5V6H9V2.5a.5.5 0 0 0-.5-.5h-1Zm-.5 5h5v2.5a3 3 0 1 1-6 0V7Z" fill="currentColor"/>',
    
    // Tools & Maintenance
    Wrench: '<path d="M15.62 3.34a4.38 4.38 0 0 0-5.2 6.74l-6.59 6.58a1.5 1.5 0 0 0 2.13 2.12l6.58-6.58a4.38 4.38 0 0 0 6.78-5.16.5.5 0 0 0-.84-.12l-2.22 2.22-1.24-.35-.35-1.24 2.22-2.22a.5.5 0 0 0-.12-.84 4.37 4.37 0 0 0-1.15-.15Zm-3.5 2.04a2.87 2.87 0 0 1 3.7-.62l-1.54 1.54a.75.75 0 0 0-.18.75l.6 2.1c.08.3.32.53.6.6l2.1.6c.27.08.56 0 .76-.17l1.54-1.54a2.88 2.88 0 0 1-3.66 3.66.75.75 0 0 0-.82.16l-6.9 6.9a.5.5 0 0 1-.7-.7l6.9-6.9a.75.75 0 0 0 .16-.82 2.87 2.87 0 0 1 .44-3.56Z" fill="currentColor"/>',
    
    // Temperature & Climate
    Temperature: '<path d="M10 2a2.5 2.5 0 0 0-2.5 2.5v6.38a4 4 0 1 0 5 0V4.5A2.5 2.5 0 0 0 10 2ZM8.5 4.5a1.5 1.5 0 0 1 3 0v6.88c0 .23.1.44.28.58a3 3 0 1 1-3.56 0c.18-.14.28-.35.28-.58V4.5Zm2.25 6a.75.75 0 0 0-1.5 0v2.58a1.5 1.5 0 1 0 1.5 0V10.5Z" fill="currentColor"/>',
    Fire: '<path d="M10.92 2.19a.75.75 0 0 0-1.3.2 7.49 7.49 0 0 1-1.61 2.5 6.49 6.49 0 0 0-2.01 4.7c0 2.47 1.28 4.62 3.19 5.75a2.5 2.5 0 0 1-1.69-2.1 3.25 3.25 0 0 1 1.37-2.9.75.75 0 0 0-.11-1.27c-.42-.2-.75-.55-.93-.96a5.32 5.32 0 0 1 3.09-1.73.75.75 0 0 0 .55-1.04c-.2-.47-.32-.98-.37-1.5a8.38 8.38 0 0 0 4.4 3.72 4.5 4.5 0 0 1-2.35 6.88 5.5 5.5 0 0 0 2.85-4.85c0-2.96-2.2-5.27-5.08-7.4Zm-.73 8.46c.58-.44.81-1.2.81-1.86-.79.25-1.48.7-2 1.3-.35.4-.5.84-.5 1.25 0 .82.4 1.52 1 1.9a2.5 2.5 0 0 1 .69-2.59Z" fill="currentColor"/>',
    
    // Meters & Gauges
    Gauge: '<path d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16Zm-6.5 8a6.5 6.5 0 1 1 13 0 6.5 6.5 0 0 1-13 0ZM10 5.25a.75.75 0 0 1 .75.75v2.69l1.78 1.78a.75.75 0 1 1-1.06 1.06l-2-2A.75.75 0 0 1 9.25 9V6c0-.41.34-.75.75-.75Z" fill="currentColor"/>',
    DataPie: '<path d="M10 2a8 8 0 1 1 0 16 8 8 0 0 1 0-16Zm-.75 1.54a6.5 6.5 0 1 0 7.21 7.21H10.5a.75.75 0 0 1-.75-.75V3.54Zm1.5.07v5.64h5.64a6.52 6.52 0 0 0-5.64-5.64Z" fill="currentColor"/>',
    
    // Smart Home
    SmartHome: '<path d="M10.45 2.24a.75.75 0 0 0-.9 0l-7 5.25A.75.75 0 0 0 2.25 8v8c0 .97.78 1.75 1.75 1.75h3.25a.75.75 0 0 0 .75-.75v-4.5h4v4.5c0 .41.34.75.75.75H16c.97 0 1.75-.78 1.75-1.75V8a.75.75 0 0 0-.3-.6l-7-5.25ZM16.25 8.31V16a.25.25 0 0 1-.25.25h-2.5v-4.5a.75.75 0 0 0-.75-.75h-5.5a.75.75 0 0 0-.75.75v4.5H4a.25.25 0 0 1-.25-.25V8.31L10 3.81l6.25 4.5Z" fill="currentColor"/>',
    
    // Radiator/Heating
    Radiator: '<path d="M4 4a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2H4Zm-.5 2c0-.28.22-.5.5-.5h12c.28 0 .5.22.5.5v8a.5.5 0 0 1-.5.5H4a.5.5 0 0 1-.5-.5V6ZM5 7a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5V7Zm4-.5a.5.5 0 0 0-.5.5v6a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5V7a.5.5 0 0 0-.5-.5H9Zm3.5.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5V7Z" fill="currentColor"/>',
    
    // Shields & Protection
    Shield: '<path d="M10.3 2.1a.75.75 0 0 0-.6 0C6.56 3.48 4.5 4.39 2.78 4.94a.75.75 0 0 0-.53.72v4.84c0 3.58 2.55 6.47 7.45 8.4a.75.75 0 0 0 .6 0c4.9-1.93 7.45-4.82 7.45-8.4V5.66a.75.75 0 0 0-.53-.72C15.5 4.4 13.44 3.48 10.3 2.1ZM3.75 6.25c1.64-.56 3.51-1.39 6.25-2.64 2.74 1.25 4.61 2.08 6.25 2.64V10.5c0 2.86-2.02 5.24-6.25 6.93-4.23-1.69-6.25-4.07-6.25-6.93V6.25Z" fill="currentColor"/>',
    ShieldCheckmark: '<path d="M10.3 2.1a.75.75 0 0 0-.6 0C6.56 3.48 4.5 4.39 2.78 4.94a.75.75 0 0 0-.53.72v4.84c0 3.58 2.55 6.47 7.45 8.4a.75.75 0 0 0 .6 0c4.9-1.93 7.45-4.82 7.45-8.4V5.66a.75.75 0 0 0-.53-.72C15.5 4.4 13.44 3.48 10.3 2.1ZM3.75 6.25c1.64-.56 3.51-1.39 6.25-2.64 2.74 1.25 4.61 2.08 6.25 2.64V10.5c0 2.86-2.02 5.24-6.25 6.93-4.23-1.69-6.25-4.07-6.25-6.93V6.25Zm9.03 2.97a.75.75 0 1 0-1.06-1.06L9 10.88l-1.22-1.22a.75.75 0 1 0-1.06 1.06l1.75 1.75c.3.3.77.3 1.06 0l3.25-3.25Z" fill="currentColor"/>'
};

// Default icon mapping for common field types
const DEFAULT_ICONS: Record<string, { yes: string; no: string }> = {
    default: { yes: "Checkmark", no: "Dismiss" },
    home: { yes: "ShieldCheckmark", no: "Home" },
    car: { yes: "Car", no: "Car" },
    ev: { yes: "PlugConnected", no: "Car" },
    meter: { yes: "Gauge", no: "Gauge" },
    thermostat: { yes: "Temperature", no: "Temperature" },
    radiator: { yes: "Fire", no: "Radiator" },
    repair: { yes: "Wrench", no: "Warning" }
};

export class FeatureTile implements ComponentFramework.StandardControl<IInputs, IOutputs> {
    private container!: HTMLDivElement;
    private notifyOutputChanged!: () => void;
    private tileEl!: HTMLButtonElement;
    private iconEl!: HTMLSpanElement;
    private labelEl!: HTMLSpanElement;

    // Current state
    private currentValue: boolean | null = null;
    private isDisabled = false;
    private isReadOnly = false;
    private iconYes = "Checkmark";
    private iconNo = "Dismiss";
    private labelText = "";
    private tileSize = "medium";

    // Track last rendered state to avoid unnecessary DOM updates
    private lastRenderedIconName = "";
    private lastRenderedClassName = "";
    private lastRenderedLabel = "";

    // Flag to prevent update loops
    private isPendingOutput = false;

    private onClickBound!: (ev: MouseEvent) => void;

    constructor() {
        // Empty
    }

    public init(
        context: ComponentFramework.Context<IInputs>,
        notifyOutputChanged: () => void,
        state: ComponentFramework.Dictionary,
        container: HTMLDivElement
    ): void {
        this.container = container;
        this.notifyOutputChanged = notifyOutputChanged;

        // Create tile button
        this.tileEl = document.createElement("button");
        this.tileEl.type = "button";
        this.tileEl.className = "mjpcf-featureTile mjpcf-featureTile--medium mjpcf-featureTile--unknown";
        this.tileEl.setAttribute("role", "switch");
        this.tileEl.setAttribute("aria-checked", "mixed");

        // Create icon container
        this.iconEl = document.createElement("span");
        this.iconEl.className = "mjpcf-featureTile__icon";

        // Create label
        this.labelEl = document.createElement("span");
        this.labelEl.className = "mjpcf-featureTile__label";

        this.tileEl.appendChild(this.iconEl);
        this.tileEl.appendChild(this.labelEl);
        this.container.appendChild(this.tileEl);

        this.onClickBound = (ev: MouseEvent) => {
            ev.preventDefault();
            ev.stopPropagation();
            this.toggle();
        };

        this.tileEl.addEventListener("click", this.onClickBound);

        this.updateFromContext(context);
        this.render(true); // Force initial render
    }

    public updateView(context: ComponentFramework.Context<IInputs>): void {
        // Skip if we just triggered this via notifyOutputChanged
        if (this.isPendingOutput) {
            this.isPendingOutput = false;
            return;
        }

        this.updateFromContext(context);
        this.render(false);
    }

    public getOutputs(): IOutputs {
        return {
            value: this.currentValue === null ? undefined : this.currentValue
        };
    }

    public destroy(): void {
        if (this.tileEl && this.onClickBound) {
            this.tileEl.removeEventListener("click", this.onClickBound);
        }
    }

    private toggle(): void {
        if (this.isDisabled || this.isReadOnly) {
            return;
        }

        if (this.currentValue === null) {
            this.currentValue = true;
        } else {
            this.currentValue = !this.currentValue;
        }

        this.render(true); // Force render after toggle
        this.isPendingOutput = true;
        this.notifyOutputChanged();
    }

    private updateFromContext(context: ComponentFramework.Context<IInputs>): void {
        this.isDisabled = context.mode.isControlDisabled;

        const security = context.parameters.value.security;
        this.isReadOnly = security ? !security.editable : false;

        // Get bound value - be very strict about type coercion
        const raw = context.parameters.value.raw;
        let newValue: boolean | null;
        if (raw === null || raw === undefined) {
            newValue = null;
        } else if (typeof raw === "boolean") {
            newValue = raw;
        } else if (typeof raw === "number") {
            newValue = raw !== 0;
        } else {
            newValue = null;
        }
        this.currentValue = newValue;

        // Get configuration properties with fallbacks
        this.iconYes = context.parameters.iconYes?.raw || "Checkmark";
        this.iconNo = context.parameters.iconNo?.raw || "Dismiss";
        this.labelText = context.parameters.labelText?.raw || "";

        const sizeRaw = (context.parameters.tileSize?.raw || "medium").toLowerCase();
        if (sizeRaw === "small" || sizeRaw === "s") {
            this.tileSize = "small";
        } else if (sizeRaw === "large" || sizeRaw === "l") {
            this.tileSize = "large";
        } else {
            this.tileSize = "medium";
        }
    }

    private render(force: boolean): void {
        const base = "mjpcf-featureTile";
        const sizeClass = `${base}--${this.tileSize}`;
        const stateClass =
            this.currentValue === true
                ? `${base}--yes`
                : this.currentValue === false
                ? `${base}--no`
                : `${base}--unknown`;
        const disabledClass = (this.isDisabled || this.isReadOnly) ? `${base}--disabled` : "";

        const newClassName = [base, sizeClass, stateClass, disabledClass].filter(Boolean).join(" ");

        // Determine icon
        let iconName: string;
        let ariaChecked: string;
        if (this.currentValue === true) {
            iconName = this.iconYes;
            ariaChecked = "true";
        } else if (this.currentValue === false) {
            iconName = this.iconNo;
            ariaChecked = "false";
        } else {
            iconName = "Question";
            ariaChecked = "mixed";
        }

        // Only update DOM if something changed (or forced)
        if (force || newClassName !== this.lastRenderedClassName) {
            this.tileEl.className = newClassName;
            this.tileEl.disabled = this.isDisabled;
            this.tileEl.setAttribute("aria-checked", ariaChecked);
            this.lastRenderedClassName = newClassName;
        }

        // Only update icon if changed (expensive innerHTML operation)
        if (force || iconName !== this.lastRenderedIconName) {
            const iconPath = FLUENT_ICONS[iconName] || FLUENT_ICONS["Question"];
            this.iconEl.innerHTML = `<svg viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" fill="currentColor">${iconPath}</svg>`;
            this.lastRenderedIconName = iconName;
        }

        // Only update label if changed
        const newLabel = this.labelText || "";
        if (force || newLabel !== this.lastRenderedLabel) {
            if (newLabel) {
                this.labelEl.textContent = newLabel;
                this.labelEl.style.display = "block";
                this.tileEl.setAttribute("aria-label", `${newLabel}: ${this.getStateLabel()}`);
            } else {
                this.labelEl.textContent = "";
                this.labelEl.style.display = "none";
                this.tileEl.setAttribute("aria-label", this.getStateLabel());
            }
            this.lastRenderedLabel = newLabel;
        }
    }

    private getStateLabel(): string {
        if (this.currentValue === true) {
            return "Yes";
        } else if (this.currentValue === false) {
            return "No";
        }
        return "Not set";
    }
}
