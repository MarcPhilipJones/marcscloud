import { IInputs, IOutputs } from "./generated/ManifestTypes";

/**
 * Fluent UI icon SVG paths (20px regular variants)
 */
const ICONS: Record<string, string> = {
    Wrench: '<path d="M15.62 3.34a4.38 4.38 0 0 0-5.2 6.74l-6.59 6.58a1.5 1.5 0 0 0 2.13 2.12l6.58-6.58a4.38 4.38 0 0 0 6.78-5.16.5.5 0 0 0-.84-.12l-2.22 2.22-1.24-.35-.35-1.24 2.22-2.22a.5.5 0 0 0-.12-.84 4.37 4.37 0 0 0-1.15-.15Zm-3.5 2.04a2.87 2.87 0 0 1 3.7-.62l-1.54 1.54a.75.75 0 0 0-.18.75l.6 2.1c.08.3.32.53.6.6l2.1.6c.27.08.56 0 .76-.17l1.54-1.54a2.88 2.88 0 0 1-3.66 3.66.75.75 0 0 0-.82.16l-6.9 6.9a.5.5 0 0 1-.7-.7l6.9-6.9a.75.75 0 0 0 .16-.82 2.87 2.87 0 0 1 .44-3.56Z" fill="currentColor"/>',
    Shield: '<path d="M10.3 2.1a.75.75 0 0 0-.6 0C6.56 3.48 4.5 4.39 2.78 4.94a.75.75 0 0 0-.53.72v4.84c0 3.58 2.55 6.47 7.45 8.4a.75.75 0 0 0 .6 0c4.9-1.93 7.45-4.82 7.45-8.4V5.66a.75.75 0 0 0-.53-.72C15.5 4.4 13.44 3.48 10.3 2.1ZM3.75 6.25c1.64-.56 3.51-1.39 6.25-2.64 2.74 1.25 4.61 2.08 6.25 2.64V10.5c0 2.86-2.02 5.24-6.25 6.93-4.23-1.69-6.25-4.07-6.25-6.93V6.25Zm9.03 2.97a.75.75 0 1 0-1.06-1.06L9 10.88l-1.22-1.22a.75.75 0 1 0-1.06 1.06l1.75 1.75c.3.3.77.3 1.06 0l3.25-3.25Z" fill="currentColor"/>',
    Gauge: '<path d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16Zm-6.5 8a6.5 6.5 0 1 1 13 0 6.5 6.5 0 0 1-13 0ZM10 5.25a.75.75 0 0 1 .75.75v2.69l1.78 1.78a.75.75 0 1 1-1.06 1.06l-2-2A.75.75 0 0 1 9.25 9V6c0-.41.34-.75.75-.75Z" fill="currentColor"/>',
    Car: '<path d="M6.2 4.5A2.25 2.25 0 0 1 8.32 3h3.36c.9 0 1.73.54 2.1 1.38l.87 1.99c.06.14.15.27.27.37l1.59 1.36c.62.53.99 1.3.99 2.12V14a2 2 0 0 1-2 2h-.75a2 2 0 0 1-2-2H7.25a2 2 0 0 1-2 2H4.5a2 2 0 0 1-2-2v-3.78c0-.81.36-1.59.99-2.12l1.59-1.36c.12-.1.2-.23.27-.37l.86-1.99.02-.04-.03.17Zm6.4 1.1a.75.75 0 0 0-.68-.1h-3.84a.75.75 0 0 0-.68.44L6.55 8h6.9l-.85-2.4ZM4.5 14h.75a.5.5 0 0 0 .5-.5v-.25c0-.14.11-.25.25-.25h8c.14 0 .25.11.25.25v.25c0 .28.22.5.5.5h.75a.5.5 0 0 0 .5-.5v-3.78a.75.75 0 0 0-.28-.58l-.91-.78H5.19l-.91.78a.75.75 0 0 0-.28.58V13.5c0 .28.22.5.5.5Z" fill="currentColor"/>',
    PlugConnected: '<path d="M8.5 2a.5.5 0 0 0-.5.5V6H6.5a.5.5 0 0 0-.5.5v3a4 4 0 0 0 3.5 3.97V17a1 1 0 0 0 1 1 1 1 0 0 0 1-1v-3.53A4 4 0 0 0 15 9.5v-3a.5.5 0 0 0-.5-.5H13V2.5a.5.5 0 0 0-.5-.5h-1a.5.5 0 0 0-.5.5V6H9V2.5a.5.5 0 0 0-.5-.5h-1Zm-.5 5h5v2.5a3 3 0 1 1-6 0V7Z" fill="currentColor"/>',
    Temperature: '<path d="M10 2a2.5 2.5 0 0 0-2.5 2.5v6.38a4 4 0 1 0 5 0V4.5A2.5 2.5 0 0 0 10 2ZM8.5 4.5a1.5 1.5 0 0 1 3 0v6.88c0 .23.1.44.28.58a3 3 0 1 1-3.56 0c.18-.14.28-.35.28-.58V4.5Zm2.25 6a.75.75 0 0 0-1.5 0v2.58a1.5 1.5 0 1 0 1.5 0V10.5Z" fill="currentColor"/>',
    Fire: '<path d="M10.92 2.19a.75.75 0 0 0-1.3.2 7.49 7.49 0 0 1-1.61 2.5 6.49 6.49 0 0 0-2.01 4.7c0 2.47 1.28 4.62 3.19 5.75a2.5 2.5 0 0 1-1.69-2.1 3.25 3.25 0 0 1 1.37-2.9.75.75 0 0 0-.11-1.27c-.42-.2-.75-.55-.93-.96a5.32 5.32 0 0 1 3.09-1.73.75.75 0 0 0 .55-1.04c-.2-.47-.32-.98-.37-1.5a8.38 8.38 0 0 0 4.4 3.72 4.5 4.5 0 0 1-2.35 6.88 5.5 5.5 0 0 0 2.85-4.85c0-2.96-2.2-5.27-5.08-7.4Zm-.73 8.46c.58-.44.81-1.2.81-1.86-.79.25-1.48.7-2 1.3-.35.4-.5.84-.5 1.25 0 .82.4 1.52 1 1.9a2.5 2.5 0 0 1 .69-2.59Z" fill="currentColor"/>',
    Heart: '<path d="M10 5.76a4.06 4.06 0 0 0-5.76-.27 4.06 4.06 0 0 0 0 5.75l5.23 5.23c.3.29.77.29 1.06 0l5.23-5.23a4.06 4.06 0 0 0-5.76-5.48Zm4.7 4.42L10 14.88l-4.7-4.7a2.56 2.56 0 1 1 3.62-3.63l.55.55c.3.3.77.3 1.06 0l.55-.55a2.56 2.56 0 1 1 3.63 3.63Z" fill="currentColor"/>',
    Question: '<path d="M10 2a8 8 0 1 1 0 16 8 8 0 0 1 0-16Zm0 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13ZM10 13a1 1 0 1 1 0 2 1 1 0 0 1 0-2Zm0-7.5c1.52 0 2.75 1.23 2.75 2.75 0 .9-.43 1.7-1.1 2.2l-.15.11-.25.17c-.4.29-.5.47-.5.77a.75.75 0 0 1-1.5 0c0-.92.47-1.53 1.15-2.02l.26-.18.1-.07c.33-.24.49-.54.49-.98a1.25 1.25 0 0 0-2.5 0 .75.75 0 0 1-1.5 0C7.25 6.73 8.48 5.5 10 5.5Z" fill="currentColor"/>'
};

/**
 * Tile configuration - hardcoded field mappings
 */
interface TileConfig {
    propertyName: keyof IInputs;
    label: string;
    icon: string;
}

const TILE_CONFIG: TileConfig[] = [
    // Row 1
    { propertyName: "repairedRecently", label: "Repaired", icon: "Wrench" },
    { propertyName: "homeCareCover", label: "HomeCare", icon: "Shield" },
    { propertyName: "smartMeter", label: "Smart Meter", icon: "Gauge" },
    { propertyName: "evOwner", label: "EV Owner", icon: "Car" },
    // Row 2
    { propertyName: "homeEvCharger", label: "EV Charger", icon: "PlugConnected" },
    { propertyName: "hiveThermostat", label: "Hive", icon: "Temperature" },
    { propertyName: "smartRadiatorValves", label: "Smart Valves", icon: "Fire" },
    { propertyName: "priorityRegister", label: "Priority", icon: "Heart" }
];

export class PCFGridMJ implements ComponentFramework.StandardControl<IInputs, IOutputs> {
    private container!: HTMLDivElement;
    private notifyOutputChanged!: () => void;
    private gridEl!: HTMLDivElement;
    private tiles = new Map<string, HTMLButtonElement>();
    
    // Current values for each field
    private values = new Map<string, boolean | null>();
    private pendingChanges = new Map<string, boolean | null>();
    
    private isDisabled = false;
    private isPendingOutput = false;

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

        // Create grid container
        this.gridEl = document.createElement("div");
        this.gridEl.className = "mjpcf-grid";

        // Create tiles for each field
        TILE_CONFIG.forEach((config, index) => {
            const tile = this.createTile(config, index);
            this.tiles.set(config.propertyName, tile);
            this.gridEl.appendChild(tile);
        });

        this.container.appendChild(this.gridEl);
        this.updateFromContext(context);
        this.renderAll();
    }

    private createTile(config: TileConfig, index: number): HTMLButtonElement {
        const tile = document.createElement("button");
        tile.type = "button";
        tile.className = "mjpcf-grid__tile mjpcf-grid__tile--unknown";
        tile.setAttribute("role", "switch");
        tile.setAttribute("aria-checked", "mixed");
        tile.setAttribute("data-property", config.propertyName);
        tile.tabIndex = 0;

        // Icon
        const iconEl = document.createElement("span");
        iconEl.className = "mjpcf-grid__icon";
        const iconPath = ICONS[config.icon] || ICONS["Question"];
        iconEl.innerHTML = `<svg viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">${iconPath}</svg>`;

        // Label
        const labelEl = document.createElement("span");
        labelEl.className = "mjpcf-grid__label";
        labelEl.textContent = config.label;

        tile.appendChild(iconEl);
        tile.appendChild(labelEl);

        // Click handler
        tile.addEventListener("click", (ev) => {
            ev.preventDefault();
            ev.stopPropagation();
            this.toggleTile(config.propertyName);
        });

        return tile;
    }

    private toggleTile(propertyName: string): void {
        if (this.isDisabled) return;

        const currentValue = this.values.get(propertyName);
        let newValue: boolean;
        
        if (currentValue === null || currentValue === undefined) {
            newValue = true;
        } else {
            newValue = !currentValue;
        }

        this.values.set(propertyName, newValue);
        this.pendingChanges.set(propertyName, newValue);
        this.renderTile(propertyName);
        
        this.isPendingOutput = true;
        this.notifyOutputChanged();
    }

    public updateView(context: ComponentFramework.Context<IInputs>): void {
        if (this.isPendingOutput) {
            this.isPendingOutput = false;
            return;
        }

        this.updateFromContext(context);
        this.renderAll();
    }

    private updateFromContext(context: ComponentFramework.Context<IInputs>): void {
        this.isDisabled = context.mode.isControlDisabled;

        // Read all bound field values
        TILE_CONFIG.forEach((config) => {
            const param = context.parameters[config.propertyName as keyof IInputs];
            if (param) {
                const raw = (param as ComponentFramework.PropertyTypes.TwoOptionsProperty).raw;
                let value: boolean | null;
                if (raw === null || raw === undefined) {
                    value = null;
                } else if (typeof raw === "boolean") {
                    value = raw;
                } else if (typeof raw === "number") {
                    value = raw !== 0;
                } else {
                    value = null;
                }
                this.values.set(config.propertyName, value);
            }
        });
    }

    private renderAll(): void {
        TILE_CONFIG.forEach((config) => {
            this.renderTile(config.propertyName);
        });
    }

    private renderTile(propertyName: string): void {
        const tile = this.tiles.get(propertyName);
        if (!tile) return;

        const value = this.values.get(propertyName);
        const base = "mjpcf-grid__tile";
        
        let stateClass: string;
        let ariaChecked: string;

        if (value === true) {
            stateClass = `${base}--yes`;
            ariaChecked = "true";
        } else if (value === false) {
            stateClass = `${base}--no`;
            ariaChecked = "false";
        } else {
            stateClass = `${base}--unknown`;
            ariaChecked = "mixed";
        }

        const disabledClass = this.isDisabled ? `${base}--disabled` : "";
        tile.className = [base, stateClass, disabledClass].filter(Boolean).join(" ");
        tile.disabled = this.isDisabled;
        tile.setAttribute("aria-checked", ariaChecked);
    }

    public getOutputs(): IOutputs {
        const outputs: IOutputs = {};
        
        // Only output fields that have pending changes
        this.pendingChanges.forEach((value, propertyName) => {
            (outputs as Record<string, boolean | undefined>)[propertyName] = 
                value === null ? undefined : value;
        });
        
        // Clear pending changes after output
        this.pendingChanges.clear();
        
        return outputs;
    }

    public destroy(): void {
        this.tiles.forEach((tile) => {
            tile.remove();
        });
        this.tiles.clear();
    }
}
