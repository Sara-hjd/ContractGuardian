// Interface de ContractGuardian (F6) : importer un contrat, lire ses clauses, poser des questions.
// Chaque résultat affiche le passage cité avec sa page et ses positions (traçabilité, règle 1).
import { useEffect, useState } from 'react'
import './App.css'

const API = '/api'

async function appeler(chemin, options = {}) {
  const reponse = await fetch(API + chemin, options)
  const donnees = await reponse.json().catch(() => ({}))
  if (!reponse.ok) throw new Error(donnees.detail || `Erreur ${reponse.status}`)
  return donnees
}

function Citation({ page, debut, fin, texte }) {
  return (
    <blockquote className="citation">
      <div className="provenance">Page {page} · positions {debut}–{fin}</div>
      {texte}
    </blockquote>
  )
}

function Clauses({ contratId }) {
  const [clauses, setClauses] = useState(null)
  useEffect(() => { appeler(`/contrats/${contratId}/clauses`).then((d) => setClauses(d.clauses)) }, [contratId])
  if (!clauses) return <p>Chargement…</p>
  if (clauses.length === 0) return <p>Aucune clause détectée.</p>
  const familles = [...new Set(clauses.map((c) => c.famille))]
  return familles.map((f) => (
    <section key={f}>
      <h3>{f} ({clauses.filter((c) => c.famille === f).length})</h3>
      {clauses.filter((c) => c.famille === f).map((c) => (
        <div key={c.segment_id + f}>
          <small>score {c.score} · modèle {c.modele}</small>
          <Citation page={c.page} debut={c.debut} fin={c.fin} texte={c.citation} />
        </div>
      ))}
    </section>
  ))
}

function Questions({ contratId }) {
  const [question, setQuestion] = useState('')
  const [mode, setMode] = useState('rag')
  const [reponse, setReponse] = useState(null)
  const [attente, setAttente] = useState(false)
  async function envoyer(e) {
    e.preventDefault()
    setAttente(true); setReponse(null)
    try {
      setReponse(await appeler(`/contrats/${contratId}/questions`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, mode }),
      }))
    } catch (err) { setReponse({ erreur: err.message }) }
    setAttente(false)
  }
  return (
    <div>
      <form onSubmit={envoyer} className="question">
        <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Question en anglais, par ex. What is the notice period to terminate?" />
        <select value={mode} onChange={(e) => setMode(e.target.value)}>
          <option value="rag">LLM local + citations vérifiées</option>
          <option value="extractif">Extractif (segment cité)</option>
        </select>
        <button disabled={attente || question.length < 3}>{attente ? 'Recherche…' : 'Demander'}</button>
      </form>
      {reponse?.erreur && <p className="erreur">{reponse.erreur}</p>}
      {reponse && !reponse.erreur && (reponse.abstention
        ? <p className="abstention">Pas de réponse fiable dans ce contrat ({reponse.raison}).</p>
        : <div>
            {reponse.reponse && <p><strong>Réponse :</strong> {reponse.reponse}</p>}
            {reponse.citations.map((c, i) => <Citation key={i} page={c.page} debut={c.debut} fin={c.fin} texte={c.extrait} />)}
          </div>)}
    </div>
  )
}

function Alertes({ contratId }) {
  const [donnees, setDonnees] = useState(null)
  useEffect(() => { appeler(`/contrats/${contratId}/alertes`).then(setDonnees).catch((e) => setDonnees({ erreur: e.message })) }, [contratId])
  if (!donnees) return <p>Analyse des paires de clauses…</p>
  if (donnees.erreur) return <p className="erreur">{donnees.erreur}</p>
  return (
    <div>
      <p className="experimental">Expérimental : {donnees.note}</p>
      {donnees.alertes.length === 0 && <p>Aucun point à vérifier signalé.</p>}
      {donnees.alertes.map((a, i) => (
        <section key={i} className="alerte">
          <h4>Point à vérifier ({a.raisons.join(', ')})</h4>
          <Citation page={a.clause_a.page} debut={a.clause_a.debut} fin={a.clause_a.fin} texte={a.clause_a.citation} />
          <Citation page={a.clause_b.page} debut={a.clause_b.debut} fin={a.clause_b.fin} texte={a.clause_b.citation} />
        </section>
      ))}
    </div>
  )
}

function Nli({ contratId }) {
  const [hypothese, setHypothese] = useState('')
  const [resultat, setResultat] = useState(null)
  async function envoyer(e) {
    e.preventDefault()
    setResultat(await appeler(`/contrats/${contratId}/nli`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ hypothese }),
    }).catch((err) => ({ erreur: err.message })))
  }
  return (
    <div>
      <form onSubmit={envoyer} className="question">
        <input value={hypothese} onChange={(e) => setHypothese(e.target.value)} placeholder="Hypothèse, par ex. Receiving Party shall not reverse engineer any objects." />
        <button disabled={hypothese.length < 3}>Vérifier</button>
      </form>
      {resultat?.erreur && <p className="erreur">{resultat.erreur}</p>}
      {resultat && !resultat.erreur && (
        <div>
          <p><strong>{resultat.etiquette}</strong> (score {resultat.score}) — <small>{resultat.note}</small></p>
          {resultat.evidences.map((e) => <Citation key={e.segment_id} page={e.page} debut={e.debut} fin={e.fin} texte={e.citation} />)}
        </div>
      )}
    </div>
  )
}

export default function App() {
  const [contrats, setContrats] = useState([])
  const [choisi, setChoisi] = useState(null)
  const [onglet, setOnglet] = useState('clauses')
  const [message, setMessage] = useState('')
  const [avertissement, setAvertissement] = useState('')

  const recharger = () => appeler('/contrats').then((d) => { setContrats(d.contrats); setAvertissement(d.avertissement) })
    .catch((e) => setMessage(`API indisponible : ${e.message}`))
  useEffect(() => { recharger() }, [])

  async function importer(e) {
    const fichier = e.target.files[0]
    if (!fichier) return
    setMessage(`Import de ${fichier.name}… (extraction, segments, clauses)`)
    const formulaire = new FormData()
    formulaire.append('fichier', fichier)
    try {
      const r = await appeler('/contrats', { method: 'POST', body: formulaire })
      setMessage(`${r.titre} : ${r.nb_pages} pages, ${r.segments} segments, ${r.clauses_detectees} clauses détectées` +
        (r.pages_sans_texte.length ? ` ; pages sans texte (scan ?) : ${r.pages_sans_texte.join(', ')}` : ''))
      await recharger(); setChoisi(r.id)
    } catch (err) { setMessage(`Échec de l'import : ${err.message}`) }
  }

  return (
    <div className="page">
      <header>
        <h1>ContractGuardian</h1>
        <p className="avertissement">{avertissement || 'Aide à la lecture : pas un avis juridique.'}</p>
      </header>
      <div className="corps">
        <aside>
          <label className="import">Importer un contrat PDF<input type="file" accept="application/pdf" onChange={importer} /></label>
          {message && <p className="message">{message}</p>}
          <ul>
            {contrats.map((c) => (
              <li key={c.id} className={c.id === choisi ? 'choisi' : ''} onClick={() => setChoisi(c.id)}>
                {c.titre} <small>({c.nb_pages} p.)</small>
              </li>
            ))}
          </ul>
        </aside>
        <main>
          {!choisi ? <p>Choisissez ou importez un contrat.</p> : (
            <>
              <nav>
                {[['clauses', 'Clauses'], ['questions', 'Questions'], ['alertes', 'Alertes (expérimental)'], ['nli', 'Hypothèse (NLI)']].map(([cle, nom]) => (
                  <button key={cle} className={onglet === cle ? 'actif' : ''} onClick={() => setOnglet(cle)}>{nom}</button>
                ))}
              </nav>
              {onglet === 'clauses' && <Clauses contratId={choisi} />}
              {onglet === 'questions' && <Questions contratId={choisi} />}
              {onglet === 'alertes' && <Alertes contratId={choisi} />}
              {onglet === 'nli' && <Nli contratId={choisi} />}
            </>
          )}
        </main>
      </div>
    </div>
  )
}
