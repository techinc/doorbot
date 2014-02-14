/*
 * Copyright (c) 2013 Erik Bosman <erik@minemu.org>
 *
 * Permission  is  hereby  granted,  free  of  charge,  to  any  person
 * obtaining  a copy  of  this  software  and  associated documentation
 * files (the "Software"),  to deal in the Software without restriction,
 * including  without  limitation  the  rights  to  use,  copy,  modify,
 * merge, publish, distribute, sublicense, and/or sell copies of the
 * Software,  and to permit persons to whom the Software is furnished to
 * do so, subject to the following conditions:
 *
 * The  above  copyright  notice  and this  permission  notice  shall be
 * included  in  all  copies  or  substantial portions  of the Software.
 *
 * THE SOFTWARE  IS  PROVIDED  "AS IS", WITHOUT WARRANTY  OF ANY KIND,
 * EXPRESS OR IMPLIED,  INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY,  FITNESS  FOR  A  PARTICULAR  PURPOSE  AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
 * BE LIABLE FOR ANY CLAIM,  DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT,  TORT OR OTHERWISE,  ARISING FROM, OUT OF OR IN
 * CONNECTION  WITH THE SOFTWARE  OR THE USE  OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 * (http://opensource.org/licenses/mit-license.html)
 */

#define TIMEOUT       (5000)  /* ms */
#define DEBOUNCE_TIME (40)    /* ms */

#define LOCK_PIN    (A0)
#define SENSOR_PIN  (10)
#define LED_PIN     (13)

enum
{
	LED_ON = LOW,
	LED_OFF = HIGH,
};

enum
{
	DOOR_UNLOCKED = LOW,
	DOOR_LOCKED = HIGH,

} lock_state;

enum
{
	DOOR_OPEN = HIGH,
	DOOR_CLOSED = LOW,

};
uint8_t sensor_state;

unsigned long cur, unlock_time, event_time;
uint8_t debounce = 0;

void lock_door(void)
{
	digitalWrite(LED_PIN, LED_OFF);
	digitalWrite(LOCK_PIN, DOOR_LOCKED);
	lock_state = DOOR_LOCKED;
}

void unlock_door(void)
{
	digitalWrite(LED_PIN, LED_ON);
	digitalWrite(LOCK_PIN, DOOR_UNLOCKED);
	lock_state = DOOR_UNLOCKED;
	unlock_time = cur;
}

/*
 * Sensor
 */

void print_sensor_state(void)
{
	if (sensor_state == DOOR_OPEN)
		Serial.println("OPEN");
	else
		Serial.println("CLOSED");
}

void sensor_poll()
{
	uint8_t s = digitalRead(SENSOR_PIN);
	if (s != sensor_state)
	{
		sensor_state = s;
		debounce = !debounce;
		event_time = cur;
	}
	if ( debounce && (cur-event_time) > DEBOUNCE_TIME)
	{
		debounce = 0;
		print_sensor_state();
	}
}

/*
 * Control commands
 */

#define MAX_COMMAND (15)
char command[MAX_COMMAND+1];
int command_len = 0;

void command_poll()
{
	int c;
	while( (c = Serial.read()) != -1 )
	{
		if ( (c == '\r') || (c == '\n') || (c == '\0') )
		{
			command[command_len] = '\0';

			if ( strcmp(command, "LOCK") == 0 )
				lock_door();

			else if ( strcmp(command, "UNLOCK") == 0 )
				unlock_door();

			else if ( strcmp(command, "STATE") == 0 )
				print_sensor_state();

			command_len = 0;
		}
		else if (command_len < MAX_COMMAND)
			command[command_len++] = c;
	}
}

void setup(void)
{
	pinMode(LED_PIN, OUTPUT);
	pinMode(LOCK_PIN, OUTPUT);
	pinMode(SENSOR_PIN, INPUT_PULLUP);
	sensor_state = digitalRead(SENSOR_PIN);
	lock_door();
	Serial.begin(9600);
	Serial.println("RESET");
	print_sensor_state();
	debounce = 0;
}

void loop(void)
{
	for(;;)
	{
		cur = millis();
		command_poll();
		if ( (lock_state == DOOR_UNLOCKED) && ( (cur-unlock_time) > TIMEOUT ) )
			lock_door();

		sensor_poll();
	}
}

