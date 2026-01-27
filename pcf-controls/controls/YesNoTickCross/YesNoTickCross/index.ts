import { IInputs, IOutputs } from "./generated/ManifestTypes";

export class YesNoTickCross implements ComponentFramework.StandardControl<IInputs, IOutputs> {
    private container!: HTMLDivElement;
    private notifyOutputChanged!: () => void;
    private buttonEl!: HTMLButtonElement;
    private iconEl!: HTMLSpanElement;

    private currentValue: boolean | null = null;
    private isDisabled = false;
    private isReadOnly = false;
    private onClickBound!: (ev: MouseEvent) => void;
    private onKeyDownBound!: (ev: KeyboardEvent) => void;

    /**
     * Empty constructor.
     */
    constructor() {
        // Empty
    }

    /**
     * Used to initialize the control instance. Controls can kick off remote server calls and other initialization actions here.
     * Data-set values are not initialized here, use updateView.
     * @param context The entire property bag available to control via Context Object; It contains values as set up by the customizer mapped to property names defined in the manifest, as well as utility functions.
     * @param notifyOutputChanged A callback method to alert the framework that the control has new outputs ready to be retrieved asynchronously.
     * @param state A piece of data that persists in one session for a single user. Can be set at any point in a controls life cycle by calling 'setControlState' in the Mode interface.
     * @param container If a control is marked control-type='standard', it will receive an empty div element within which it can render its content.
     */
    public init(
        context: ComponentFramework.Context<IInputs>,
        notifyOutputChanged: () => void,
        state: ComponentFramework.Dictionary,
        container: HTMLDivElement
    ): void {
        this.container = container;
        this.notifyOutputChanged = notifyOutputChanged;

        this.buttonEl = document.createElement("button");
        this.buttonEl.type = "button";
        this.buttonEl.className = "mjpcf-yesNoTickCross mjpcf-yesNoTickCross--unknown";
        this.buttonEl.setAttribute("role", "switch");
        this.buttonEl.setAttribute("aria-checked", "mixed");

        this.iconEl = document.createElement("span");
        this.iconEl.className = "mjpcf-yesNoTickCross__icon";
        this.iconEl.textContent = "?";

        this.buttonEl.appendChild(this.iconEl);
        this.container.appendChild(this.buttonEl);

        this.onClickBound = (ev: MouseEvent) => {
            ev.preventDefault();
            this.toggle();
        };

        this.onKeyDownBound = (ev: KeyboardEvent) => {
            if (ev.key === " " || ev.key === "Enter") {
                ev.preventDefault();
                this.toggle();
            }
        };

        this.buttonEl.addEventListener("click", this.onClickBound);
        this.buttonEl.addEventListener("keydown", this.onKeyDownBound);
        this.updateFromContext(context);
        this.render();
    }

    private toggle(): void {
        if (this.isDisabled || this.isReadOnly) {
            return;
        }

        // Toggle: null -> true, true -> false, false -> true
        if (this.currentValue === null) {
            this.currentValue = true;
        } else {
            this.currentValue = !this.currentValue;
        }

        this.render();
        this.notifyOutputChanged();
    }


    /**
     * Called when any value in the property bag has changed. This includes field values, data-sets, global values such as container height and width, offline status, control metadata values such as label, visible, etc.
     * @param context The entire property bag available to control via Context Object; It contains values as set up by the customizer mapped to names defined in the manifest, as well as utility functions
     */
    public updateView(context: ComponentFramework.Context<IInputs>): void {
        this.updateFromContext(context);
        this.render();
    }

    /**
     * It is called by the framework prior to a control receiving new data.
     * @returns an object based on nomenclature defined in manifest, expecting object[s] for property marked as "bound" or "output"
     */
    public getOutputs(): IOutputs {
        // Explicitly return undefined to clear the field when null
        return {
            value: this.currentValue === null ? undefined : this.currentValue
        };
    }

    /**
     * Called when the control is to be removed from the DOM tree. Controls should use this call for cleanup.
     * i.e. cancelling any pending remote calls, removing listeners, etc.
     */
    public destroy(): void {
        if (this.buttonEl) {
            if (this.onClickBound) {
                this.buttonEl.removeEventListener("click", this.onClickBound);
            }
            if (this.onKeyDownBound) {
                this.buttonEl.removeEventListener("keydown", this.onKeyDownBound);
            }
        }
    }

    private updateFromContext(context: ComponentFramework.Context<IInputs>): void {
        this.isDisabled = context.mode.isControlDisabled;
        
        // Check field-level security for editability
        const security = context.parameters.value.security;
        this.isReadOnly = security ? !security.editable : false;

        const raw = context.parameters.value.raw;
        if (raw === null || raw === undefined) {
            this.currentValue = null;
            return;
        }

        // TwoOptions is typically boolean, but be defensive.
        if (typeof raw === "boolean") {
            this.currentValue = raw;
        } else if (typeof raw === "number") {
            this.currentValue = raw !== 0;
        } else {
            this.currentValue = null;
        }
    }

    private render(): void {
        const base = "mjpcf-yesNoTickCross";
        const stateClass =
            this.currentValue === true
                ? `${base}--yes`
                : this.currentValue === false
                ? `${base}--no`
                : `${base}--unknown`;

        const inactiveClass = (this.isDisabled || this.isReadOnly) ? `${base}--disabled` : "";
        this.buttonEl.className = [base, stateClass, inactiveClass].filter(Boolean).join(" ");
        this.buttonEl.disabled = this.isDisabled;
        
        // Set aria-checked for switch role
        if (this.currentValue === true) {
            this.iconEl.textContent = "✓";
            this.buttonEl.setAttribute("aria-label", "Yes");
            this.buttonEl.setAttribute("aria-checked", "true");
        } else if (this.currentValue === false) {
            this.iconEl.textContent = "✕";
            this.buttonEl.setAttribute("aria-label", "No");
            this.buttonEl.setAttribute("aria-checked", "false");
        } else {
            this.iconEl.textContent = "?";
            this.buttonEl.setAttribute("aria-label", "No value");
            this.buttonEl.setAttribute("aria-checked", "mixed");
        }
    }
}
