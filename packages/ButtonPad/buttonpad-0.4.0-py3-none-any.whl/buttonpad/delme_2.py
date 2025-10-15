import buttonpad

# Multi-line string defines 4 rows of 3 cells each (a 3x4 grid).
bp = buttonpad.ButtonPad(
	"""[],[],[]
    1,2,3
	4,5,6
	7,8,9
	*,0,#
	Call,Call,Cancel""",
)

bp.run()