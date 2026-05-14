# Why Only This Founder Could Have Built Tijan With AI

The following are verbatim instructions Malick Tall sent to Claude (across Claude Code, Cowork desktop, the Claude mobile app, and Claude in Chrome) while building Tijan AI as a solo non-technical founder. Each one is a real message from his side of the conversation. None of them could have been written by someone without deep, ground-level expertise in West African construction engineering, French-language Eurocode practice, and the unspoken realities of building in markets where Silicon Valley has no presence.

---

## 1. Setting the constitution: zero hardcoding, no shortcuts, no co-founder

> *Fondateur: Serigne Malick Tall (Malick), solo non-technical founder. Mission: Premier fondateur non-technique à construire une licorne. **Règle absolue: Ne jamais suggérer d'embaucher ou de recruter un co-fondateur technique.** Règles de développement: Zéro hardcoding — toutes les valeurs viennent des calculs réels. Aucune fonction déboguée plus de 3 fois — réécrire si ça continue à échouer. Monkey-patching de ReportLab Paragraph est INTERDIT. Supabase RLS: utiliser auth.uid() = user_id + GRANT ALL explicite.*

Most non-technical founders ask AI to "make it work." Malick set hard engineering constraints from day one — no hardcoded values in a structural calculation engine, no monkey-patching of PDF libraries, explicit row-level security policies — and held the line for months.

---

## 2. The reference project that anchors every calculation

> *Projet de référence — Résidence Papa Oumar Sakho, R+8, 32 unités, Dakar, Réf. 1711. Béton C30/37 BPE 185,000 FCFA/m³, acier HA500B 520-540 FCFA/kg.*

This single sentence contains: a real Dakar project (R+8 = ground floor + 8 stories), the exact concrete grade used in Senegalese ready-mix supply, the live April 2026 market price of BPE concrete in Dakar, the rebar grade local steel mills produce, and the spread of rebar prices. No engineer outside francophone West Africa knows this. No AI knows this. Only someone embedded in the market does.

---

## 3. Catching a deliverable that "looks fine" but is engineering-wrong

> *C'est mieux par rapport au cadre mais c'est loupé pour la géométrie.*

> *On est bon pour la structure, mais il faut améliorer encore la présetation du MEP, éviter la superposition des flèches et des écritures, rendre les visuels plus propres, plus professionnels et plus beaux encore.*

> *On est quasiment bon sur le MEP à part quelques détails que tu verras ici. Pour la structure, tu as dégagé le fonds mais tu as surchargé d'éléments rendant la chose illisible.*

> *C'est mieux, on récup les plans, par contre ce qui est présenté n'est aucunement juste, lisible ou accurate. Comment on améliore cela?*

These corrections required reading a generated PDF — schematic diagrams of structural reinforcement and MEP risers — and immediately spotting that the geometry was off, that arrows overlapped, that the framing was wrong, that the architectural plan extraction had captured noise instead of walls. Spotting that means having reviewed thousands of execution drawings in your career. A non-domain founder would have shipped the broken version.

---

## 4. Refusing to estimate when accuracy matters downstream

> *Oui mais, il faut changer le point 3. Il faut demander le nombre d'appartement au upload et confirmer avec le parsing dont tu parles. **En aucun cas il ne faut estimer**, parce que cela fausse trop de données pour la suite.*

The system was guessing the apartment count from surface area. Malick caught that the guess was off (116 estimated vs. 33 actual) and immediately understood the cascading consequence: every MEP sizing downstream — water demand, electrical load, ventilation rate, fire safety provisioning — was going to be wrong. The fix wasn't to improve the guess. It was to ban the guess. That is engineering judgment, not coding instinct.

---

## 5. Knowing the market well enough to refuse a freemium model

> *Non, J'aime pas le freemium parce que le nombre de projet par entité n'est pas aussi important. Même le fait d'offrir un projet me gêne. **On est dans un environnement où la fraude est importante.** Il ne faudrait pas que les users puissent voir les outputs sans pouvoir y accéder.*

> *Que penses-tu de ceci: Starter: 1 projet → 100 000 FCFA / poste de travail; Pro: 3 projets → 225 000 FCFA / poste de travail avec projets supplémentaires à 75 000 FCFA; Entreprise: illimité + API → sur devis. Augmente significativement le prix des extras à venir et annonce-les (revue par un ingénieur, certification EDGE, autorisation de construire).*

A SF founder would have copy-pasted Stripe's pricing template. Malick knew that in Dakar, Abidjan, and Lagos, freemium leaks. He set per-seat monthly pricing in CFA francs, with credit packs for marginal projects, and reserved high-touch services (engineer review, EDGE certification, building permit dossier) as paid premium.

---

## 6. Speaking the product back into reality

> *Personnifie Tijan. Ce ne doit pas être un bureau d'étude, mais **un ingénieur de conception génie civil et électro-mécanicien**, au service de votre bureau d'étude, ou de votre étude architecturale, ou de votre société de promotion immobilière, ou de votre banque.*

> *Sur la landing page, trouve un moyen de dire que nous sommes une innovation mondiale et le seul agent bureau d'études / ingénieurs dans le monde.*

> *J'avais imaginé en animation une structure qui s'élève et du cabling et du piping qui s'enchevêtrent comme un ADN se construirait.*

The product positioning, the visual metaphor (a building rising while structural rebar, electrical cabling, and HVAC piping interweave like DNA), the personification as a civil + electro-mechanical engineer rather than a generic "engineering bureau" — all of it came from him. The AI wrote the code. The vision is his.

---

## 7. The roadmap nobody else could prioritize correctly

> *Backlog Tijan AI: 1) Géométrie DWG→plans, 2) BA rouge fix, 3) i18n EN, 4) Engineer Review v2, 5) AC digital, 6) EDGE digital, 7) Domaine tijan.ai seul, 8) LLM modif projet, 9) nb_niveaux+occupants, 10) Cohérence crédits, 11) Refonte interface revues ingénieur, 12) Outputs DWG+Excel+Word, 13) UI onglets plans, 14) Redirection achat crédit si épuisés, 15) Landing page+/impact+/investors.*

Fifteen items. Every single one is a real, in-the-trenches priority that requires you to know what an architect uploads (DWG and PDF, depending on their workflow), what a structural calculation note must contain ("BA rouge" = the red structural drawings), why the engineering review interface needs collaborative validation by two engineers before replacing an original deliverable, and why French and English must coexist because francophone Africa is bilingual at the professional level. No AI could have prioritized this list. No outsider founder could have either.

---

## 8. Pitching the impact angle nobody outside the market sees

> *Modifier les contenus de la page impact en se focalisant et en développant exclusivement les aspects de préservation de l'environnement, de développement de la certification EDGE, d'économie d'eau et d'énergie, de lutte contre le gaspillage sur les chantiers, et de la production et de la commercialisation de crédit carbone, mais aussi de la sécurité et de la durabilité des bâtiments.*

> *Revoir le contenu de la page investisseur en creusant le problème; en donnant plus de contexte sur l'urbanisation en Afrique, la contribution des bâtiments à la pollution, le potentiel d'optimisation d'énergie et d'eau. **S'assurer de la taille du marché et développer la partie sur le marché en précisant que nous ne visons pas les bâtiments disposant d'études, mais ceux bien plus importants qui n'en disposent pas.***

The single most important market insight in the entire conversation is in that last sentence. The total addressable market for engineering bureau software in West Africa is not the buildings that already pay an engineering bureau. It is the **vastly larger** segment of buildings that go up without any structural calculations at all — informal construction, fast-growing peri-urban housing, unregulated developer projects. Tijan turns a non-market into a market. That insight requires having watched West African urbanization happen with your own eyes.

---

## 9. The discipline of a founder who runs the build like a chantier

> *On y va.*
>
> *Oui commit. Pousse le tout en production et audit la plateforme. Stress-test la au maximum.*
>
> *Tu prends trop de temps et tu ne me parles pas, je sais pas si tu marches ou pas. Dis-moi ce que tu fais et donne-moi une estimation du temps que les tâches que je t'ai confiées te prendront.*
>
> *Don't stop until you deliver a fully functional platform to me.*

Malick treats the AI the way a construction site manager treats a foreman: clear instructions, status checks, no tolerance for silent stalls, and a refusal to accept "almost done." The same discipline he uses on chantiers in Dakar is what made him able to ship 15,000 lines of production Python without ever writing one himself.

---

## 10. The closing line of every iteration

> *Pushed.*
>
> *Deployed.*
>
> *Live.*

That is the rhythm of the past 11 days. He pushes. Render and Vercel deploy. He tests on the live product. He comes back with the next correction. No team. No co-founder. No technical hire. Just a non-technical founder, the deepest market knowledge anyone could have on West African construction, and Claude as the foreman.

---

## What this proves

The technical stack of Tijan (FastAPI, React, Supabase, ReportLab, ezdxf, ODA File Converter) is reproducible by any competent engineering team in two weeks. The Eurocode 2 + Eurocode 8 + French DTU encoding is reproducible by a senior structural engineer in six months. **Neither of those is the moat.**

The moat is that the only person on Earth who could have written the prompts above — who knows that BPE concrete in Dakar costs 185,000 FCFA/m³, that HA500B rebar trades at 520–540 FCFA/kg, that francophone West African projects need both DWG and PDF intake because architects use both, that the real TAM is buildings that *don't* use engineering bureaus, that fraud environments don't tolerate freemium, that "BA rouge" is the red structural drawing — happens to also be the founder of the company. And he built the entire product with Claude, alone, in French and English, in less than two weeks of focused work.

That is what AI coding tools unlock when they are placed in the hands of a domain expert who has been waiting his entire career for the leverage.
