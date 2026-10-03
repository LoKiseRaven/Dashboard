/** Contrat de `GET /api/modules` (spec §8) et de la route d'état des apps (spec §6.2). */

export type Etat = "OFF" | "STARTING" | "ON" | "WORKING" | "WAITING" | "STOPPING" | "ERROR";

export interface Tache {
  id: string;
  libelle: string;
  etape?: string | null;
  progression?: number | null;
  gpu?: boolean;
  statut: "en_cours" | "en_attente";
  position_file?: number | null;
  debut?: string | null;
}

export interface Module {
  id: string;
  nom: string;
  emoji: string;
  port: number;
  gpu: boolean;
  etat: Etat;
  message: string | null;
  taches: Tache[];
  detail_disponible: boolean;
  depuis: string;
  code_sortie: number | null;
}

export interface Session {
  connecte: boolean;
  local: boolean;
}

export const ALLUMES: Etat[] = ["ON", "WORKING", "WAITING"];
export const OCCUPES: Etat[] = ["WORKING", "WAITING"];
export const EN_TRANSITION: Etat[] = ["STARTING", "STOPPING"];
