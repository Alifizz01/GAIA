function out = build_gaia_simulink_demo(runIt)
%BUILD_GAIA_SIMULINK_DEMO  Build (and run) a Simulink model around the GAIA BMS block.
%
%   gaia_setup('...\python.exe');      % once per session
%   build_gaia_simulink_demo           % builds gaia_bms_demo.slx, runs 45 min, plots
%
%   Model: a drive-like current profile (Repeating Sequence Stair) feeds the
%   GaiaBMS System block; its seven outputs go to a scope and to the
%   workspace. Swap the source for your own controller to close the loop.
    if nargin < 1, runIt = true; end
    model = 'gaia_bms_demo';
    here = fileparts(mfilename('fullpath'));
    addpath(here);
    if bdIsLoaded(model), close_system(model, 0); end
    new_system(model); open_system(model);

    add_block('simulink/Sources/Repeating Sequence Stair', [model '/Load profile'], ...
        'OutValues', '[50 50 0 100 100 25 0 75]', 'tsamp', '60', 'Position', [40 100 120 140]);
    add_block('simulink/User-Defined Functions/MATLAB System', [model '/GAIA BMS'], ...
        'System', 'GaiaBMS', 'Position', [200 60 330 220]);
    set_param([model '/GAIA BMS'], 'CellsInSeries', '12', 'Chemistry', '''NMC''', ...
        'CapacityAh', '50', 'InitialSoc', '90', 'SampleTime', '1');
    add_line(model, 'Load profile/1', 'GAIA BMS/1');

    add_block('simulink/Signal Routing/Mux', [model '/Mux'], 'Inputs', '7', 'Position', [400 60 405 220]);
    add_block('simulink/Sinks/Scope', [model '/Scope'], 'NumInputPorts', '1', 'Position', [470 120 500 160]);
    add_block('simulink/Sinks/To Workspace', [model '/To Workspace'], 'VariableName', 'gaia', ...
        'SaveFormat', 'Timeseries', 'Position', [470 190 540 220]);
    for k = 1:7
        add_line(model, sprintf('GAIA BMS/%d', k), sprintf('Mux/%d', k));
    end
    add_line(model, 'Mux/1', 'Scope/1');
    add_line(model, 'Mux/1', 'To Workspace/1');
    set_param(model, 'StopTime', '2700', 'Solver', 'FixedStepDiscrete', 'FixedStep', '1');
    save_system(model, fullfile(here, [model '.slx']));
    fprintf('Built %s.slx\n', model);

    out = [];
    if runIt
        out = sim(model);
        d = out.gaia.Data; t = out.gaia.Time / 60;
        figure('Name', 'GAIA BMS in Simulink');
        tiledlayout(3, 1);
        nexttile; plot(t, d(:, 4), 'k--', t, d(:, 3), 'LineWidth', 1.5); ylabel('SOC [%]'); legend('true', 'BMS estimate');
        nexttile; yyaxis left; plot(t, d(:, 1)); ylabel('V'); yyaxis right; plot(t, d(:, 2)); ylabel('A');
        nexttile; plot(t, d(:, 5), 'LineWidth', 1.5); ylabel('hottest cell [degC]'); xlabel('time [min]');
        fprintf('End: SOC true %.1f %%, estimate %.1f %%, hottest cell %.1f C\n', d(end, 4), d(end, 3), max(d(:, 5)));
    end
end
