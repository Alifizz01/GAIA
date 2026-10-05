function gaia_setup(pythonExe)
%GAIA_SETUP  Point MATLAB at a Python that has GAIA installed.
%   gaia_setup('C:\path\to\.venv\Scripts\python.exe')
%   gaia_setup()   % keep MATLAB's current Python
%
%   GAIA needs Python 3.9-3.12 (PyBaMM). Install it once in that Python:
%       python -m pip install -e <GAIA repo folder>
%   Call this before anything else in a fresh MATLAB session: pyenv can only
%   change the interpreter before Python has been loaded.

    if nargin > 0 && ~isempty(pythonExe)
        pe = pyenv;
        if pe.Status == "Loaded" && ~strcmpi(pe.Executable, pythonExe)
            error('gaia:setup', ['Python is already loaded from %s. Restart MATLAB, ' ...
                  'then call gaia_setup first.'], pe.Executable);
        end
        pyenv('Version', pythonExe, 'ExecutionMode', 'OutOfProcess');
    end
    % Make the repository importable even without `pip install -e`.
    repo = fileparts(fileparts(mfilename('fullpath')));
    sysPath = py.sys.path;
    if ~any(cellfun(@(p) strcmp(char(p), repo), cell(sysPath)))
        insert(sysPath, int32(0), repo);
    end
    gaia = py.importlib.import_module('gaia');
    fprintf('GAIA %s via Python %s\n', char(gaia.('__version__')), char(pyenv().Version));
end
