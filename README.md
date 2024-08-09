Käyntiin esimerkiksi näin. Yhteen terminaaliin palvelin:

```
make run_server
```

Toiseen asiakas:

```
make run_client
```

Ja sitten vielä tts-, stt- ja llm-apit. Näin voi pyörittää localai-konttia:

```
make run_api
```

Vaihtoehtoisesti palvelimelle voi asettaa ympäristömuuttujat, esimerkiksi:
```
API_ADDRESS=https://api.openai.com
OPENAI_API_KEY=sk-<xx>
OPENAI_ORGANIZATION=org-<yy>
```

Ja sitten selaimella osoitteeseen http://localhost:3000.

