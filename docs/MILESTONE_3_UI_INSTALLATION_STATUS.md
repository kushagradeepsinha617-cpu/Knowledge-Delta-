# UI installation: packages present, pandas blocked by Windows policy

The user completed the approved normal-terminal installation command. Its report
records all 34 locked packages as installed, with full wheel SHA256 checks. The
final import check failed, so this is not a successful UI acceptance result.

## Actual observations

- Download ledger reservations: **86,786,569 bytes** of the 150,000,000-byte cap.
  Reservations conservatively include reads that may return no payload.
- Later folder inventory: **371,959,665 logical bytes**, below the approved
  750,000,000-byte ceiling. This is an observation, not a measured installation peak.
- Independent isolated imports succeeded for NumPy **2.5.4** and PyArrow **26.0.1**.
- The separate real NumPy integration suite executed **15 tests**, all passing
  (0.43 seconds). Its tokenizer and vector-producing objects are labeled test
  doubles. It does not verify Sentence Transformers, Ollama or model inference.
- Windows Code Integrity event **3077** identifies the blocked project file
  `pandas/_libs/hashtable.cp315-win_amd64.pyd` and policy
  `VerifiedAndReputableDesktop`. The signature check reports the file unsigned.
- The installed file's SHA256 matches its wheel RECORD entry. That checks byte
  consistency; it does not grant Windows execution trust or prove software safety.

The ordinary 358-test source checkpoint remains unchanged. The 15 numeric checks
are separately scoped actual dependency tests, not another ordinary-suite run or
an assistant benchmark.

## Remaining gate

The pandas native import is blocked by the operating system. The Windows Security
UI setting has not yet been confirmed by the user. The user reports this is a
personal computer; that does not establish which protection setting is active.

No policy was disabled or bypassed. No alternate loader, relocation, re-signing,
package substitution or redownload was attempted. Preserve the installed packages
and download ledger while the block is reviewed through legitimate Windows or
publisher channels. Reinstalling the same bytes is not an identified remedy.

Actual Streamlit AppTest, interface rendering and localhost startup remain
unverified. No server or model was started. No model was downloaded.

## Evidence

- [User-run installation report](evidence/milestone3-ui-installation/installation-report.json)
- [Original import failure](evidence/milestone3-ui-installation/readiness-error.txt)
- [Targeted diagnosis and independent import checks](evidence/milestone3-ui-installation/diagnosis.json)
- [Real numeric test output](evidence/milestone3-ui-installation/numpy-integration.json)
- [Numeric JUnit results](evidence/milestone3-ui-installation/numpy-integration.xml)
- [Microsoft's App Control event interpretation](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/operations/appcontrol-debugging-and-troubleshooting)
- [Microsoft's Smart App Control FAQ](https://support.microsoft.com/en-gb/windows/security/threat-malware-protection/smart-app-control-frequently-asked-questions)
