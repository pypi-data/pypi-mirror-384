Androids can be downloaded from [Dropbox](https://zenodo.org/record/7447302).

Simply download and unzip, it is already in audformat.

```bash
# Download using wget
wget https://www.dropbox.com/s/2rurxlh70ihfki4/Androids-Corpus.zip
# Unzip
unzip Androids-Corpus.zip
# delete zip file for space
rm Androids-Corpus.zip
# delete the audio sub folder, as it contains the whole interviews, including the interviewer (the data with only the patients is in the folder audio_clip)
rm -r Androids-Corpus/Interview-Task/audio
# run the script to generate the CSV file from the database
python ./process_database.py
# change to Nkululeko parent directory
cd ../..
# convert to mono 16 kHz sampling rate
python -m nkululeko.resample --config data/androids/exp.ini
# explore the data
python -m nkululeko.explore --config data/androids/exp.ini
# run the nkululeko experiment
python -m nkululeko.nkululeko --config data/androids/exp.ini
```

Then, check the results in the `results` directory.
