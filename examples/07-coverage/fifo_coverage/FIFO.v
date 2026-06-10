module FIFO #(
    parameter WIDTH = 8,
    parameter DEPTH = 4,
    parameter ADDR_WIDTH = 2
) (
    input clock,
    input reset,
    input push,
    input pop,
    input [WIDTH-1:0] data_in,
    output reg [WIDTH-1:0] data_out,
    output full,
    output empty,
    output reg [ADDR_WIDTH:0] count
);

reg [WIDTH-1:0] mem [0:DEPTH-1];
reg [ADDR_WIDTH-1:0] wr_ptr;
reg [ADDR_WIDTH-1:0] rd_ptr;

assign full = (count == DEPTH);
assign empty = (count == 0);

wire do_push = push && !full;
wire do_pop = pop && !empty;

always @(posedge clock) begin
    if (reset) begin
        wr_ptr <= 0;
        rd_ptr <= 0;
        count <= 0;
        data_out <= 0;
    end else begin
        if (do_push) begin
            mem[wr_ptr] <= data_in;
            wr_ptr <= wr_ptr + 1'b1;
        end

        if (do_pop) begin
            data_out <= mem[rd_ptr];
            rd_ptr <= rd_ptr + 1'b1;
        end

        case ({do_push, do_pop})
            2'b10: count <= count + 1'b1;
            2'b01: count <= count - 1'b1;
            default: count <= count;
        endcase
    end
end

endmodule
