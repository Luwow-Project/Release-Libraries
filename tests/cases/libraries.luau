local t = require("./harness")

local folder: string, platform: string = GlobalArgs[3], GlobalArgs[4]

t.check("task loads and waits", function()
	local task = require("@Luwow/task")
	t.equal(type(task.wait), "function", "task.wait")
	task.wait(0.01)
end)

t.check("fs writes and reads a file", function()
	local fs = require("@Luwow/fs")
	local path = `{folder}/hello.txt`
	fs.writeFile(path, "hello")
	t.equal(fs.exists(path), true, "exists")
	t.equal(fs.readFile(path), "hello", "contents")
end)

t.check("io loads", function()
	local io = require("@Luwow/io")
	t.equal(type(io.write), "function", "io.write")
end)

t.check("signal fires its connections", function()
	local signal = require("@Luwow/signal")
	local event = signal.new()
	local received = nil
	event:Connect(function(value)
		received = value
	end)
	event:Fire(5)
	t.equal(received, 5, "the fired value")
end)

t.check("net loads", function()
	local net = require("@Luwow/net")
	t.equal(type(net.request), "function", "net.request")
end)

-- No gui on Linux
if not string.find(platform, "linux", 1, true) then
	t.check("gui loads", function()
		local gui = require("@Luwow/gui")
		t.equal(type(gui.createWindow), "function", "gui.createWindow")
	end)
end

t.done()
