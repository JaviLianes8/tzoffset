// Reference output from java.time.ZoneOffset for tests/test_java_oracle.py.
// Reads lines "P <text>" (parse with ZoneOffset.of) and "F <seconds>" (format with the
// ZoneOffset id and three DateTimeFormatter offset patterns) and writes each input line,
// a tab and the result. Run through scripts/java_oracle.py.
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeFormatterBuilder;

class ZoneOffsetOracle {
    public static void main(String[] args) throws Exception {
        DateTimeFormatter colon = DateTimeFormatter.ofPattern("xxxxx");
        DateTimeFormatter compact = DateTimeFormatter.ofPattern("xxxx");
        DateTimeFormatter shortForm =
            new DateTimeFormatterBuilder().appendOffset("+HH:mm:ss", "+00").toFormatter();
        BufferedReader in =
            new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
        StringBuilder out = new StringBuilder();
        for (String line; (line = in.readLine()) != null; ) {
            String arg = line.substring(2);
            out.append(line).append('\t');
            if (line.charAt(0) == 'P') {
                try {
                    out.append(ZoneOffset.of(arg).getTotalSeconds());
                } catch (Exception e) {
                    out.append("ERR");
                }
            } else {
                ZoneOffset z = ZoneOffset.ofTotalSeconds(Integer.parseInt(arg));
                out.append(z.getId()).append(' ').append(colon.format(z)).append(' ')
                    .append(compact.format(z)).append(' ').append(shortForm.format(z));
            }
            out.append('\n');
        }
        System.out.print(out);
    }
}
