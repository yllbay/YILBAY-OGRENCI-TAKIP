function driveTokenSavePatch(patch){const old=readStoredSecrets();return writeSecrets({...old,...patch})}
