%GAIA_MATLAB_EXAMPLE  Discharge a pack, overheat a cell, watch the BMS trip and recover.
%   Run gaia_setup('...\python.exe') first in a fresh MATLAB session.

pack = GaiaPack(12, "NMC", 50, 90);
pack.setCurrent(50);                          % 1C discharge
T1 = pack.runFor(1200);                       % 20 minutes

pack.injectFault(5, "overheat");              % cell 5 to 65 degC
T2 = pack.runFor(60);
fprintf('Latched faults: %s\n', strjoin(pack.faults(), ', '));
fprintf('Reset while hot accepted? %d\n', pack.resetFault());

pack.injectFault(5, "heal");
pack.runFor(5);
fprintf('Reset after cooling accepted? %d\n', pack.resetFault());
pack.setCurrent(50);
T3 = pack.runFor(1200);

T = [T1; T2; T3];
figure('Name', 'GAIA pack from MATLAB');
tiledlayout(3, 1);
nexttile; plot(T.time_s/60, T.soc_true_pct, 'k--', T.time_s/60, T.soc_estimated_pct, 'LineWidth', 1.5);
ylabel('SOC [%]'); legend('true', 'BMS estimate'); title('GAIA: 12s NMC pack under BMS control');
nexttile; plot(T.time_s/60, T.pack_current_A, 'LineWidth', 1.5); ylabel('current [A]');
nexttile; plot(T.time_s/60, T.max_temperature_C, 'LineWidth', 1.5); ylabel('hottest cell [degC]'); xlabel('time [min]');
