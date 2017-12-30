# DynaKnock

Automatic pattern detection of unknown sound and input signal generation library

When two types of short sounds (knock sounds) are regularly generated, the pattern is automatically detected, the two kinds of sounds are registered, and each sound thereafter becomes an input signal of `A(0)` and `B(1)` .

MFCC(Mel-frequency cepstral coefficients) is used as a feature quantity of speech signal analysis. In this library, the similarity is calculated by using Euclidean distance between each sound.

By default, it detects patterns of `A,A,A B,B,B`.
This pattern can be changed by rewriting the member variable of `Dynaknock.py`.
```python
class Analyzer(object):
    ~
    EXPECT_PATTERN = [1,1,1,0,0,0]  # AAABBB
    # e.g) ABABABAB -> [1,0,1,0,1,0,1,0]
```

## Demo

working with **[MagicTV](https://github.com/Hikaru-Ito/MagicTV)**

[![YouTube](https://img.youtube.com/vi/U99A5ZwkCjI/0.jpg)](https://www.youtube.com/watch?v=U99A5ZwkCjI)

## Install
**Quick Install**

`pip` is necessary to solve the dependency.
Since the pip module required for `requirements.txt` is described, install it all together with the following command.

```sh
pip install -r reqirements.txt
```


## Usage

### Start the server
Connection waiting for TCP socket is started on `7777` port.
Processing will not proceed until client connection is made. At this point, analysis has not been done yet.

```sh
$ python server.py
```

**Only one client can connect at the same time.**
It is operating in single thread.
If the connection from the client expires, you can not connect newly unless you restart the script. This specification will be improved, but it will stay like this once.


### Client connection
Connect with TCP client. Once the connection is established, acoustic signal analysis will begin and TCP packets will be sent.

Please use any kind of TCP client.
Below is an example using a telnet client.
```sh
$ telnet localhost 7777
```

## Event signal

**`register`**

It is called when a pattern is detected.
```
{"event": "register"}
```

**`knock`**

```
{"type": false, "event": "knock"}
{"type": "A",   "event": "knock"}
{"type": "B",   "event": "knock"}
```

Called when a knock is detected. There are 3 types of attributes `A`, `B`, `false`.
`A`, `B` are cases where pattern detection has been completed.
false is when the pattern is detected, but neither sound is detected. Or if the pattern is not detected.

**`clear_knock_list`**

```
{"event": "clear_knock_list"}
```

If knocking sound does not occur for `2 seconds(AUTO_CLEAR_SEC)` or more without detecting the pattern, the sound list to be detected is cleared.

**`unregister`**

```
{"event": "unregister"}
```
If no registered knock sound occurs for `10 seconds` or more, the pattern detection is canceled.