/**
 * React hooks for contact data operations.
 *
 * Wraps the contactService facade in React state management with
 * loading, error, and refresh semantics.
 */

import { useCallback, useEffect, useState } from "react";
import type { Contact, ContactFormData } from "../types";
import {
  getAllContacts,
  getContactById,
  createContact,
  updateContact,
  deleteContact,
} from "../services/contactService";

// ── useContactList ──────────────────────────────────────────────

interface UseContactListReturn {
  contacts: Contact[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Fetches and caches the full active contact list.
 * Call `refresh()` to re-fetch after mutations.
 */
export function useContactList(): UseContactListReturn {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAllContacts({
        filter: "statecode eq 0",
        top: 250,
        orderBy: ["fullname asc"],
      });
      setContacts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load contacts");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { contacts, loading, error, refresh };
}

// ── useContact ──────────────────────────────────────────────────

interface UseContactReturn {
  contact: Contact | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Fetches a single contact by ID.
 */
export function useContact(contactId: string | undefined): UseContactReturn {
  const [contact, setContact] = useState<Contact | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!contactId) {
      setContact(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getContactById(contactId);
      setContact(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load contact");
    } finally {
      setLoading(false);
    }
  }, [contactId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { contact, loading, error, refresh };
}

// ── useContactMutations ─────────────────────────────────────────

interface UseContactMutationsReturn {
  creating: boolean;
  updating: boolean;
  deleting: boolean;
  error: string | null;
  create: (data: ContactFormData) => Promise<Contact>;
  update: (id: string, changes: Partial<ContactFormData>) => Promise<void>;
  remove: (id: string) => Promise<void>;
}

/**
 * Provides create/update/delete operations with loading state.
 * Pair with `useContactList().refresh()` after mutations.
 */
export function useContactMutations(): UseContactMutationsReturn {
  const [creating, setCreating] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const create = useCallback(
    async (data: ContactFormData): Promise<Contact> => {
      setCreating(true);
      setError(null);
      try {
        return await createContact(data);
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : "Failed to create contact";
        setError(msg);
        throw err;
      } finally {
        setCreating(false);
      }
    },
    [],
  );

  const update = useCallback(
    async (id: string, changes: Partial<ContactFormData>): Promise<void> => {
      setUpdating(true);
      setError(null);
      try {
        await updateContact(id, changes);
      } catch (err) {
        const msg =
          err instanceof Error ? err.message : "Failed to update contact";
        setError(msg);
        throw err;
      } finally {
        setUpdating(false);
      }
    },
    [],
  );

  const remove = useCallback(async (id: string): Promise<void> => {
    setDeleting(true);
    setError(null);
    try {
      await deleteContact(id);
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "Failed to delete contact";
      setError(msg);
      throw err;
    } finally {
      setDeleting(false);
    }
  }, []);

  return { creating, updating, deleting, error, create, update, remove };
}
