/*******************************************************************************
 * Copyright 2024 Zero ASIC Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * ----
 *
 * Documentation:
 * - Simple umi demux testbench
 *
 ******************************************************************************/

module testbench (
`ifdef VERILATOR
    input clk
`endif
);

`include "switchboard.vh"

    localparam M  = 4;
    localparam DW = 256;
    localparam CW = 32;
    localparam AW = 64;

    localparam PERIOD_CLK   = 10;

`ifndef VERILATOR
    // Generate clock for non verilator sim tools
    reg clk;

    initial
        clk  = 1'b0;
    always #(PERIOD_CLK/2) clk = ~clk;
`endif

    // Initialize UMI
    integer valid_mode, ready_mode;

    initial begin
        /* verilator lint_off IGNOREDRETURN */
        if (!$value$plusargs("valid_mode=%d", valid_mode)) begin
            valid_mode = 2;  // default if not provided as a plusarg
        end

        if (!$value$plusargs("ready_mode=%d", ready_mode)) begin
            ready_mode = 2;  // default if not provided as a plusarg
        end
        /* verilator lint_on IGNOREDRETURN */
    end

    wire [M-1:0]    select;

    wire            umi_in_valid;
    wire [CW-1:0]   umi_in_cmd;
    wire [AW-1:0]   umi_in_dstaddr;
    wire [AW-1:0]   umi_in_srcaddr;
    wire [DW-1:0]   umi_in_data;
    wire            umi_in_ready;

    wire [M-1:0]    umi_out_valid;
    wire [M*CW-1:0] umi_out_cmd;
    wire [M*AW-1:0] umi_out_dstaddr;
    wire [M*AW-1:0] umi_out_srcaddr;
    wire [M*DW-1:0] umi_out_data;
    wire [M-1:0]    umi_out_ready;

    ///////////////////////////////////////////
    // Host side umi agents
    ///////////////////////////////////////////

    genvar          i;

    queue_to_umi_sim #(
        .VALID_MODE_DEFAULT (2),
        .DW                 (DW)
    ) umi_rx_i (
        .clk        (clk),

        .valid      (umi_in_valid),
        .cmd        (umi_in_cmd),
        .dstaddr    (umi_in_dstaddr),
        .srcaddr    (umi_in_srcaddr),
        .data       (umi_in_data),
        .ready      (umi_in_ready)
    );

    assign select = {{(M-1){1'b0}}, 1'b1}<<umi_in_dstaddr[40+:$clog2(M)];

    initial begin
        `ifndef VERILATOR
            #1;
        `endif
        umi_rx_i.init("client2rtl_0.q");
        umi_rx_i.set_valid_mode(valid_mode);
    end

    generate
    for(i = 0; i < M; i = i + 1) begin: demux_out
        umi_to_queue_sim #(
            .READY_MODE_DEFAULT (2),
            .DW                 (DW)
        ) umi_tx_i (
            .clk        (clk),

            .valid      (umi_out_valid[i]),
            .cmd        (umi_out_cmd[i*CW+:CW]),
            .dstaddr    (umi_out_dstaddr[i*AW+:AW]),
            .srcaddr    (umi_out_srcaddr[i*AW+:AW]),
            .data       (umi_out_data[i*DW+:DW]),
            .ready      (umi_out_ready[i])
        );

        initial begin
            `ifndef VERILATOR
                #1;
            `endif
            demux_out[i].umi_tx_i.init($sformatf("rtl2client_%0d.q", i));
            demux_out[i].umi_tx_i.set_ready_mode(ready_mode);
        end
    end
    endgenerate

    // UMI Demux
    umi_demux #(
        .M  (M),
        .DW (DW),
        .CW (CW),
        .AW (AW)
    ) umi_demux_i (
        .select             (select),

        .umi_in_valid       (umi_in_valid),
        .umi_in_cmd         (umi_in_cmd),
        .umi_in_dstaddr     (umi_in_dstaddr),
        .umi_in_srcaddr     (umi_in_srcaddr),
        .umi_in_data        (umi_in_data),
        .umi_in_ready       (umi_in_ready),

        .umi_out_valid      (umi_out_valid),
        .umi_out_cmd        (umi_out_cmd),
        .umi_out_dstaddr    (umi_out_dstaddr),
        .umi_out_srcaddr    (umi_out_srcaddr),
        .umi_out_data       (umi_out_data),
        .umi_out_ready      (umi_out_ready)
    );

    // waveform dump
    `SB_SETUP_PROBES

    // auto-stop
    auto_stop_sim auto_stop_sim_i (.clk(clk));

endmodule
