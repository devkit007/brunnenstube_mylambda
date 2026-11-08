# 🚀 AWS Lambda Entwicklungs-Workflow (WSL & VS Code)

Dieses Repository enthält den Quellcode und die Infrastruktur-Konfiguration (Infrastruktur als Code) für das Lambda-Projekt **Brunnenstube/Pumproom**. Die Entwicklung, das Testen und die Versionierung finden vollständig im **Windows-Subsystem für Linux (WSL)** statt.

---

## 🛠️ Erstmaliges Setup & Onboarding

### 1. Git & GitHub SSH-Schlüssel einrichten
Da das Projekt im WSL läuft, wird ein separater Linux-SSH-Schlüssel für GitHub benötigt.

1. Neuen Ed25519-Schlüssel im WSL-Terminal generieren:
   ```bash
   ssh-keygen -t ed25519 -C "github-wsl"
   ```
   *(Abfragen mit `Enter` bestätigen).*
2. Den öffentlichen Schlüssel anzeigen und komplett kopieren:
   ```bash
   cat ~/.ssh/ed25519.pub
   ```
3. Den kopierten Schlüssel auf [GitHub](https://github.com) unter **Settings -> SSH and GPG keys -> New SSH Key** hinterlegen.

### 2. SSH-Konfigurationsdatei anpassen (`~/.ssh/config`)
Damit GitHub und andere Git-Dienste (wie AWS CodeCommit) friedlich nebeneinander existieren, muss die Konfiguration im WSL sauber getrennt werden.

1. Datei öffnen: `code ~/.ssh/config`
2. Folgenden Inhalt einfügen und speichern:
   ```text
   # GitHub-Konfiguration
   Host github.com
       HostName github.com
       User git
       IdentityFile ~/.ssh/id_ed25519
       IdentitiesOnly yes

   # AWS CodeCommit-Konfiguration
   Host git-codecommit.*.amazonaws.com
       User APKAXHTSYVFU2ZG7VMFR
       IdentityFile ~/.ssh/id_rsa
       IdentitiesOnly yes
   ```

### 3. Repository klonen
```bash
git clone git@github.com:devkit007/brunnenstube_mylambda.git
cd brunnenstube_mylambda
code .
```
*(Sicherstellen, dass VS Code im **WSL-Modus** läuft – blauer Kasten unten links im Editor).*

### 4. AWS-Zugangsdaten (Credentials) hinterlegen
Lokale Tests greifen auf echte AWS-Testressourcen zu. Dafür werden die persönlichen IAM-Benutzer-Schlüssel aus der AWS-Konsole benötigt.

1. **Keys besorgen:** In der AWS-Konsole ganz oben rechts auf den eigenen **IAM-Benutzernamen -> Security credentials -> Access keys -> Create access key** (Verwendungszweck: *CLI*) klicken und die `.csv`-Datei herunterladen.
2. **Im WSL eintragen:** Die AWS-Konfigurationsdatei im WSL öffnen:
   ```bash
   code ~/.aws/credentials
   ```
3. Die neuen Schlüssel im Block `[default]` hinterlegen:
   ```text
   [default]
   aws_access_key_id = AKIA...YourNewAccessKey...
   aws_secret_access_key = ...YourNewSecretKey...
   ```
4. Die Region in der Konfiguration prüfen (`code ~/.aws/config`):
   ```text
   [default]
   region = eu-north-1
   output = json
   ```

---

## 💻 Täglicher Entwickler-Workflow

### 1. Code bearbeiten & Lokal testen (SAM & Docker)
Änderungen werden lokal vorgenommen. Zum Testen nutzen wir ein simuliertes IoT-SPS-Event, das über AWS SAM in einen lokalen Linux-Docker-Container geschossen wird:

* **Docker-Status prüfen:** `docker ps` (Muss ohne Fehler antworten; Docker läuft nativ im WSL).
* **Lokalen Test ausführen:**
  ```bash
  sam local invoke "PumproomFunction" -e events/test-event.json
  ```
  *Hinweis:* Dank der Umgebungsvariablen in der `template.yaml` schreibt der lokale Test vollautomatisch und isoliert in die echten AWS-Testtabellen (`pumproom_data_test` [Historie mit Sort-Key `timestamp`] und `pumproom_latest_test` [Live-Zustand]), ohne die Produktionsdaten zu gefährden.

### 2. Datenbestand im Terminal prüfen
Um die geschriebenen Zeilen in der Historie-Testtabelle ohne Browser-Verzögerung zu prüfen:
```bash
aws dynamodb scan --table-name pumproom_data_test --region eu-north-1 --query "Items[*].{ID: device_id, Time: timestamp}" --output table
```

### 3. Versionierung & Git (Code-Stand sichern)
Wenn der lokale Test erfolgreich war, wird der Stand auf GitHub gesichert:
```bash
git add lambda_function.py template.yaml events/test-event.json
git commit -m "feat: beschreibung deiner änderung"
git push origin main
```

### 4. Deployment (Nach AWS pushen)
Sobald das Feature stabil ist, kann der Code auf die echte Lambda-Funktion in der Cloud übertragen werden:
* **Via SAM:** `sam deploy`
* **Via VS Code:** Rechtsklick auf die Funktion im *AWS Toolkit Explorer* -> **Sync/Deploy to AWS**.
