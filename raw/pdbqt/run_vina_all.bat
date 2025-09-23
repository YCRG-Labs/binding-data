@echo off
set vina_exe=vina
set receptor=TLR4.pdbqt
set config=config.txt

:: Create main output folders
if not exist pdbqt_outputs mkdir pdbqt_outputs
if not exist logs mkdir logs

:: Subfolders for sorting by affinity threshold
if not exist pdbqt_outputs\affinity_leq_-5 mkdir pdbqt_outputs\affinity_leq_-5
if not exist pdbqt_outputs\affinity_gt_-5 mkdir pdbqt_outputs\affinity_gt_-5
if not exist logs\affinity_leq_-5 mkdir logs\affinity_leq_-5
if not exist logs\affinity_gt_-5 mkdir logs\affinity_gt_-5

:: CSV files for summaries
echo Ligand,Affinity_kcal_mol,Category> logs\affinity_leq_-5\summary.csv
echo Ligand,Affinity_kcal_mol,Category> logs\affinity_gt_-5\summary.csv

:: Set binding affinity cutoff
set cutoff=-5.0

echo Starting docking, sorting, and CSV generation...

for %%f in (*.pdbqt) do (
    if /I not "%%f"=="%receptor%" (
        echo Docking %%~nf...
        :: Run Vina and save temporary output
        %vina_exe% --receptor %receptor% --ligand "%%f" --config %config% --out "pdbqt_outputs\temp_%%~nf.pdbqt" > "logs\temp_log_%%~nf.txt"

        :: Get the top binding affinity from the log
        for /f "tokens=4" %%a in ('findstr /C:"REMARK VINA RESULT" "logs\temp_log_%%~nf.txt"') do (
            set top_affinity=%%a
            goto :process
        )

        :process
        setlocal enabledelayedexpansion
        set affinity=!top_affinity!
        if !affinity! LEQ %cutoff% (
            echo %%~nf has affinity !affinity! kcal/mol (≤ -5)
            move "pdbqt_outputs\temp_%%~nf.pdbqt" "pdbqt_outputs\affinity_leq_-5\%%~nf.pdbqt"
            move "logs\temp_log_%%~nf.txt" "logs\affinity_leq_-5\%%~nf.txt"
            >> logs\affinity_leq_-5\summary.csv echo %%~nf,!affinity!,affinity_leq_-5
        ) else (
            echo %%~nf has affinity !affinity! kcal/mol (> -5)
            move "pdbqt_outputs\temp_%%~nf.pdbqt" "pdbqt_outputs\affinity_gt_-5\%%~nf.pdbqt"
            move "logs\temp_log_%%~nf.txt" "logs\affinity_gt_-5\%%~nf.txt"
            >> logs\affinity_gt_-5\summary.csv echo %%~nf,!affinity!,affinity_gt_-5
        )
        endlocal
    )
)

echo Docking, sorting, and CSV generation complete.
pause
