"""Liste des sources du corpus documentaire explicatif (F5, D-023).

Place dans le projet : la **seule** liste des documents explicatifs autorisés (18 sources validées par
Sara le 2026-11-26). Ce fichier ne contient **aucun texte** des sources : seulement leurs références,
leur licence et l'attribution à afficher (obligatoire pour CC BY-SA et CC BY, D-023). Le texte est
téléchargé par ``cg.explicatif.collecte`` dans ``data/raw/explicatif/`` (jamais commité).
"""

from dataclasses import dataclass
from typing import Literal

TypeSource = Literal["wikipedia", "govuk", "pdf", "far"]

WIKIPEDIA_ATTRIBUTION = "Wikipedia contributors, « {titre} », Wikipedia, The Free Encyclopedia"
CC_BY_SA = "CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)"
OGL = "Open Government Licence v3.0 (https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)"


@dataclass(frozen=True)
class Source:
    """Une source du corpus explicatif.

    Attributes:
        cle: Identifiant court et stable (nom de fichier, clé en base).
        titre: Titre de la source.
        url: Page de référence (celle citée à l'utilisateur).
        editeur: Éditeur ou auteurs.
        licence: Licence vérifiée (D-023).
        type: Manière de la télécharger et de la découper.
        adresse: Adresse de téléchargement (titre d'article, chemin GOV.UK ou URL du PDF).
        date_publication: Date de publication ou de mise à jour déclarée par l'éditeur (pour Wikipédia,
            la date de la révision téléchargée est ajoutée à la collecte).
    """

    cle: str
    titre: str
    url: str
    editeur: str
    licence: str
    type: TypeSource
    adresse: str
    date_publication: str = ""

    @property
    def attribution(self) -> str:
        """Texte d'attribution affiché à côté de chaque passage cité (D-023)."""
        auteur = WIKIPEDIA_ATTRIBUTION.format(titre=self.titre) if self.type == "wikipedia" else f"{self.editeur}, « {self.titre} »"
        return f"{auteur}. {self.url} — licence {self.licence}."


def _wikipedia(cle: str, titre: str) -> Source:
    url = "https://en.wikipedia.org/wiki/" + titre.replace(" ", "_")
    return Source(cle, titre, url, "Wikipedia contributors", CC_BY_SA, "wikipedia", titre)


SOURCES: tuple[Source, ...] = (
    _wikipedia("wp-nda", "Non-disclosure agreement"),
    _wikipedia("wp-confidentiality", "Confidentiality"),
    _wikipedia("wp-trade-secret", "Trade secret"),
    _wikipedia("wp-breach", "Breach of contract"),
    _wikipedia("wp-termination-convenience", "Termination for convenience"),
    _wikipedia("wp-fundamental-breach", "Fundamental breach"),
    _wikipedia("wp-rescission", "Rescission (contract law)"),
    _wikipedia("wp-exclusion-clause", "Exclusion clause"),
    _wikipedia("wp-indemnity", "Indemnity"),
    _wikipedia("wp-liquidated-damages", "Liquidated damages"),
    _wikipedia("wp-consequential-damages", "Consequential damages"),
    _wikipedia("wp-force-majeure", "Force majeure"),
    Source("govuk-nda", "Non-disclosure agreements",
           "https://www.gov.uk/government/publications/non-disclosure-agreements/non-disclosure-agreements",
           "UK Intellectual Property Office", OGL, "govuk",
           "government/publications/non-disclosure-agreements/non-disclosure-agreements", "2015-03-12"),
    Source("govuk-ip-confidentiality", "Managing Intellectual Property and Confidentiality",
           "https://www.gov.uk/government/publications/managing-intellectual-property-and-confidentiality",
           "UK Government (GOV.UK)", OGL, "pdf",
           "https://assets.publishing.service.gov.uk/media/6489e0be5f7bb700127faa59/Guide_to_Managing_Intellectual_Property_and_Confidentiality.pdf",
           "2023-04-17"),
    Source("govuk-risk-allocation", "Risk Allocation and Pricing Approaches guidance note",
           "https://www.gov.uk/government/publications/the-sourcing-and-consultancy-playbooks/risk-allocation-and-pricing-approaches-guidance-note-html",
           "Cabinet Office / Government Commercial Function", OGL, "govuk",
           "government/publications/the-sourcing-and-consultancy-playbooks/risk-allocation-and-pricing-approaches-guidance-note-html",
           "2026-11-05"),
    Source("govuk-msc-guidance", "Model Services Contract – Guidance for Buyers (v2.2A)",
           "https://www.gov.uk/government/publications/guidance-on-the-model-services-contract",
           "Cabinet Office, Government Legal Department", OGL, "pdf",
           "https://assets.publishing.service.gov.uk/media/68af2474960e2d135b4c8eb2/Buyer_Guidance_-_MSC_v2.2A_2025.pdf",
           "2025-09-01"),
    Source("far-part-49", "FAR Part 49 — Termination of Contracts", "https://www.acquisition.gov/far/part-49",
           "U.S. General Services Administration", "Domaine public (œuvre du gouvernement fédéral américain, 17 U.S.C. § 105)",
           "far", "https://www.acquisition.gov/far/part-49", "2026-03-13 (FAC 2026-01)"),
    Source("wipo-trade-secrets", "WIPO Guide to Trade Secrets and Innovation",
           "https://www.wipo.int/publications/en/details.jsp?id=4748", "World Intellectual Property Organization (WIPO)",
           "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)", "pdf",
           "https://www.wipo.int/edocs/pubdocs/en/wipo-pub-2008-en-wipo-guide-to-trade-secrets-and-innovation.pdf", "2024"),
)
