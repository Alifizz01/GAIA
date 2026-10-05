classdef GaiaBMS < matlab.System
%GAIABMS  GAIA's simulated pack and BMS as a Simulink block.
%
%   Use it in a "MATLAB System" block (Simulate using: Interpreted execution,
%   because the physics runs in Python). Input: requested pack current [A]
%   (positive = discharge). Outputs, in order:
%     1 pack voltage [V]       2 actual pack current [A] (0 when a contactor is open)
%     3 SOC, BMS estimate [%]  4 SOC, true [%]
%     5 hottest cell [degC]    6 BMS state (0 idle, 1 charging, 2 discharging, 4 fault, 5 emergency)
%     7 fault latched (0/1)
%   build_gaia_simulink_demo builds a ready-to-run model around it.

    properties (Nontunable)
        CellsInSeries = 12      % Cells in series
        Chemistry = 'NMC'       % Chemistry: NMC, LFP or NCA
        CapacityAh = 50         % Cell capacity [Ah]
        InitialSoc = 80         % Initial SOC [%]
        AmbientC = 25           % Ambient temperature [degC]
        SampleTime = 1          % Sample time [s]
    end

    properties (Access = private)
        Pack
    end

    methods (Access = protected)
        function setupImpl(obj)
            bridge = py.importlib.import_module('gaia.matlab_bridge');
            obj.Pack = bridge.MatlabPack(obj.CellsInSeries, obj.Chemistry, obj.CapacityAh, ...
                                         obj.InitialSoc, obj.AmbientC);
        end

        function [v, i, socEst, socTrue, tMax, state, fault] = stepImpl(obj, current)
            obj.Pack.set_current(current);
            y = cellfun(@double, cell(obj.Pack.step(obj.SampleTime)));
            v = y(1); i = y(2); socEst = y(3); socTrue = y(4); tMax = y(5); state = y(6); fault = y(9);
        end

        function resetImpl(obj)
            setupImpl(obj);
        end

        function n = getNumOutputsImpl(~)
            n = 7;
        end

        function varargout = getOutputSizeImpl(~)
            varargout = repmat({[1 1]}, 1, 7);
        end

        function varargout = getOutputDataTypeImpl(~)
            varargout = repmat({'double'}, 1, 7);
        end

        function varargout = isOutputComplexImpl(~)
            varargout = repmat({false}, 1, 7);
        end

        function varargout = isOutputFixedSizeImpl(~)
            varargout = repmat({true}, 1, 7);
        end

        function sts = getSampleTimeImpl(obj)
            sts = createSampleTime(obj, 'Type', 'Discrete', 'SampleTime', obj.SampleTime);
        end

        function names = getOutputNamesImpl(~)
            names = ["V"; "I"; "SOC est"; "SOC true"; "T max"; "state"; "fault"];
        end

        function name = getInputNamesImpl(~)
            name = "I request";
        end
    end

    methods (Static, Access = protected)
        function simMode = getSimulateUsingImpl
            simMode = "Interpreted execution";
        end

        function flag = showSimulateUsingImpl
            flag = false;
        end
    end
end
