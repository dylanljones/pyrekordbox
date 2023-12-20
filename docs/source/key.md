# Database key

If the automatic key extraction fails the command line interface of ``pyrekordbox``
provides a command for downloading the key from known sources and writing it to the
cache file:
````shell
python -m pyrekordbox download-key
````
Once the key is cached the database can be opened without providing the key.
if you obtained the key from another source, you can also pass it to the database handler
````python
db = Rekordbox6Database(key="<insert key here>")
````
or write it to the cache file manually:
````python
from pyrekordbox.config import write_db6_key_cache

write_db6_key_cache("<insert key here>")  # call once
db = Rekordbox6Database()
````

## Alternative methods

The key can be extracted manually from the users machine. After the key is obtained
it can be writen to the cache file as described above.
The method varies depending on the operating system.

### Windows

On Windows, the key can be extracted from the Rekordbox executable using a debugger:

1. Download [x64dbg] and run it.

2. Options -> Preferences. Make sure "Entry Breakpoint" is set in the Events tab.

3. File -> Open... `rekordbox.exe` (the main application executable)

4. Look at the status bar. It should have a yellow "Paused" icon followed by some status text.
   Right now it should say "System breakpoint reached!"

5. Hit F9 or press the Run button in the top bar. The status text should change to
   "INT3 breakpoint 'entry breakpoint' at <rekordbox.EntryPoint>".

6. Click in the disassembly window, then press Ctrl+G to open the Go To Expression box,
   and search for `sqlite3_key_v2` and press OK. This should jump you to the code for
   that function, which typically starts with `mov dword ptr ss:[rsp+xx], r9d` or similar.

7. Without clicking anywhere on the disassembly window, press F2 to toggle breakpoint.
   The top instruction's address should turn red.

8. Hit F9 or press the Run button in the top bar. The status text will start changing
   a bunch, while the program starts up. Wait until the status bar goes back to "Paused"
   in yellow. If the status text says something like "First chance exception on..."
   press F9 again.

9. The status bar should go to "Paused" in yellow again, this time with status text
   that says "INT3 breakpoint at <sqlite3.sqlite3_key_v2>". This means our breakpoint
   has been hit.

10. Click the register panel (top right, where RAX, RBX, RCX, etc. are listed) so
   it updates. Right click the red address next to R8, and click "Follow in dump".

11. The dump at the bottom left will move to that address. Right click the dump panel
   and select Text -> ASCII at the bottom. You should now see the key as a string.
   You can drag-select it, then right click to copy selected line.

12. Go to Debug -> Close to close the process, then close x64dbg.


```{figure} /_static/images/x64dbg_rb_key.png
:align: center
:scale: 60
```


### MacOS

On MacOS, the key can be extracted using the [RekordLocksmith] tool:

1. Install LLDB:
   - LLDB can be installed with Xcode on macOS via the App Store or xcode-cli-commands.
   - Ensure LLDB is accessible from the terminal by running `lldb` in the terminal.

2. Disable SIP:
   - Restart your Mac and hold down `Command-R` as it boots to enter Recovery Mode.
   - Open the Terminal from the Utilities menu.
   - Type `csrutil disable` and press Enter.
   - Restart your Mac.

3. Download RekordLocksmith:
   - Clone or download the [RekordLocksmith] repository from GitHub.

4. Run RekordLocksmith:
   - Use the terminal to navigate to the folder containing `rekordlocksmith.py`.
   - Run the script:
     ````shell
     python3 rekordlocksmith.py /Applications/rekordbox\ 6/rekordbox.app/Contents/MacOS/rekordbox
     ````
     The tool will output the database key to the terminal and save it to a file named `rekordbox_db_pass.txt` in the current directory.


[x64dbg]: https://x64dbg.com/
[RekordLocksmith]: https://github.com/Bide-UK/rekordlocksmith#rekordlocksmith
