rm logs
touch logs
python SpecMechSimulator.py 1079 >>logs &
python SpecMechSimulator.py 1081 >>logs &
python CamForthSimulator.py 2079 >>logs &
python CamForthSimulator.py 2080 >>logs &
tail -f logs