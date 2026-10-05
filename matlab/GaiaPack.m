classdef GaiaPack < handle
%GAIAPACK  A simulated battery pack under GAIA's BMS, driven from MATLAB.
%
%   gaia_setup('...\python.exe')                 % once per session
%   pack = GaiaPack(12, "NMC", 50, 80);          % 12s NMC, 50 Ah cells, 80 % SOC
%   pack.setCurrent(50);                         % A, positive = discharge
%   T = pack.runFor(1800);                       % table, one row per second
%   plot(T.time_s/60, [T.soc_true_pct T.soc_estimated_pct])
%   pack.injectFault(3, "overheat");             % overheat | short | fade | heal
%   y = pack.step(1)                             % one step, struct of outputs
%
%   The physics and the BMS run in Python (gaia.matlab_bridge); MATLAB only
%   converts numbers, so results match GAIA Studio and the Python API exactly.

    properties (SetAccess = private)
        Py      % the gaia.matlab_bridge.MatlabPack object
        Names   % output names, in the order step() returns them
    end

    methods
        function obj = GaiaPack(cellsInSeries, chemistry, capacityAh, initialSoc, ambientC)
            arguments
                cellsInSeries (1,1) double = 12
                chemistry (1,1) string = "NMC"
                capacityAh (1,1) double = 50
                initialSoc (1,1) double = 80
                ambientC (1,1) double = 25
            end
            bridge = py.importlib.import_module('gaia.matlab_bridge');
            obj.Py = bridge.MatlabPack(cellsInSeries, chemistry, capacityAh, initialSoc, ambientC);
            obj.Names = string(cell(bridge.OUTPUTS));
        end

        function setCurrent(obj, amps)
            obj.Py.set_current(amps);
        end

        function y = step(obj, dt)
            %STEP  Advance dt seconds (default 1). Returns a struct.
            if nargin < 2, dt = 1; end
            v = cellfun(@double, cell(obj.Py.step(dt)));
            y = cell2struct(num2cell(v(:)), cellstr(obj.Names), 1);
        end

        function T = runFor(obj, seconds, dt)
            %RUNFOR  Run with the present current request; returns a table.
            if nargin < 3, dt = 1; end
            r = obj.Py.run_for(seconds, dt);
            names = ["time_s", obj.Names];
            cols = cellfun(@(n) cellfun(@double, cell(r{char(n)}))', cellstr(names), 'UniformOutput', false);
            T = table(cols{:}, 'VariableNames', cellstr(names));
        end

        function injectFault(obj, cell, kind)
            obj.Py.inject_fault(cell, kind);
        end

        function ok = resetFault(obj)
            ok = logical(obj.Py.reset_fault());
        end

        function f = faults(obj)
            f = string(cell(obj.Py.faults()));
        end

        function s = cellSoc(obj)
            s = cellfun(@double, cell(obj.Py.cell_soc()));
        end
    end
end
