export interface IChatWidgetStore {
  isOpen: boolean;
  close(): void;
  open(): void;
  toggle(): void;
}
