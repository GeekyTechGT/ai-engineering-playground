Creami una libreria python 'jira-client' che permette di eseguire tutte le possibili operazioni su atlassian jira cloud.
Questa libreria deve essere installabile tramite pip, devi quindi definire in modo completo il file pyproject.toml per poterlo installare tramite pip install -e . , ad esempio devi implementare api per leggere il file .env per estrarre jira token, jira email, jira project, per limitare in caso di errori dell'llm, perche l'idea è far creare a claude il contenuto degli issue jira ma farli creare a questa libreria python in una pipeline che verrà chiamata da un server mcp che devo implementare. Crea codice python seguendo principi solid, pep8, e crea pure una folder con esempi per ogni api che l'utente puo utilizzare. Attieniti alla documentazione ufficiale JIRA per capire quali sono i campi necessari.
Possibili operazioni richieste dall'utente:
- estrarre tutti i progetti jira
- creare issue
- leggere open issue
- leggere closed issue in un intervallo temporale
  
Poi sugerisci te quali operazioni potrebbero essere necessarie.