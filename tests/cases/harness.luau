--[[
	The checks' reporter. Each check prints PASS or FAIL with its name, and done() prints DONE with the
	number that failed, which run_tests.py reads.
]]
local Harness = {}

local failed = 0

function Harness.check(name: string, fn: () -> ())
	local ok, err = pcall(fn)
	if ok then
		print(`PASS {name}`)
	else
		failed += 1
		print(`FAIL {name}: {err}`)
	end
end

function Harness.equal(actual: any, expected: any, what: string?)
	if actual ~= expected then
		error(`{what or "value"}: expected {tostring(expected)}, got {tostring(actual)}`, 2)
	end
end

-- fn must raise an error, whose message contains pattern (a plain string) when given
function Harness.fails(fn: () -> any, pattern: string?)
	local ok, err = pcall(fn)
	if ok then
		error("expected an error, got none", 2)
	end
	if pattern and not string.find(tostring(err), pattern, 1, true) then
		error(`expected an error containing "{pattern}", got: {err}`, 2)
	end
end

function Harness.done()
	print(`DONE {failed}`)
end

return Harness
