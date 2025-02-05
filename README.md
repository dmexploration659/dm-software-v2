# DM software

## Installation & Run

- Install node js dependencies
```
npm install
```

Then:
- go to the folder `python`
- create a virtualenv named `edtwExampleEnv`
- Activate the virtualenv

```
cd python
virtualenv edtwExampleEnv
edtwExampleEnv\Scripts\activate
```

- Install requirement python libraries
```
cd edtwExample
pip install -r requirements.txt
```

- Finally, go back to the repository root and run the desktop application
```
cd ../..
npm run start
```